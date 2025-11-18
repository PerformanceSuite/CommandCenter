import { PrismaClient, WorkflowNode } from '@prisma/client';
import { DaggerAgentExecutor } from '../dagger/executor';
import logger from '../utils/logger';

export class WorkflowRunner {
  constructor(
    private prisma: PrismaClient,
    private daggerExecutor: DaggerAgentExecutor
  ) {}

  /**
   * Topological sort of workflow nodes into execution batches
   * Nodes in the same batch can run in parallel
   */
  private topologicalSort(nodes: WorkflowNode[]): WorkflowNode[][] {
    const batches: WorkflowNode[][] = [];
    const remaining = new Set(nodes);
    const completed = new Set<string>();

    while (remaining.size > 0) {
      // Find nodes with all dependencies satisfied
      const batch: WorkflowNode[] = [];

      for (const node of remaining) {
        const allDepsCompleted = node.dependsOn.every(depId =>
          completed.has(depId)
        );

        if (allDepsCompleted) {
          batch.push(node);
        }
      }

      if (batch.length === 0) {
        throw new Error('Circular dependency detected in workflow');
      }

      // Mark batch nodes as completed
      batch.forEach(node => {
        remaining.delete(node);
        completed.add(node.id);
      });

      batches.push(batch);
    }

    return batches;
  }

  async executeWorkflow(workflowRunId: string): Promise<void> {
    const workflowRun = await this.prisma.workflowRun.findUnique({
      where: { id: workflowRunId },
      include: {
        workflow: {
          include: {
            nodes: {
              include: {
                agent: {
                  include: {
                    capabilities: true,
                  },
                },
              },
            },
          },
        },
      },
    });

    if (!workflowRun) {
      throw new Error(`WorkflowRun ${workflowRunId} not found`);
    }

    const dag = this.topologicalSort(workflowRun.workflow.nodes);

    logger.info('Executing workflow', {
      workflowRunId,
      workflowName: workflowRun.workflow.name,
      batches: dag.length,
    });

    // Execute batches sequentially, nodes in batch in parallel
    for (const batch of dag) {
      await Promise.all(
        batch.map(node => this.executeNode(node, workflowRun))
      );
    }

    // Mark workflow complete
    await this.prisma.workflowRun.update({
      where: { id: workflowRunId },
      data: {
        status: 'SUCCESS',
        finishedAt: new Date(),
      },
    });

    logger.info('Workflow completed', { workflowRunId });
  }

  private async executeNode(
    node: WorkflowNode & { agent: any },
    workflowRun: any
  ): Promise<unknown> {
    logger.info('Executing workflow node', {
      nodeId: node.id,
      agentName: node.agent.name,
    });

    // TODO: Resolve inputs from template
    const inputs = node.inputsJson;

    // TODO: Check approval if needed

    // Execute agent via Dagger
    const capability = node.agent.capabilities.find(
      (c: any) => c.name === node.action
    );

    const result = await this.daggerExecutor.executeAgent(
      node.agent.entryPath,
      inputs,
      {
        maxMemoryMb: 512,
        timeoutSeconds: 300,
        outputSchema: capability.outputSchema,
      }
    );

    // Store agent run
    await this.prisma.agentRun.create({
      data: {
        agentId: node.agentId,
        workflowRunId: workflowRun.id,
        inputJson: inputs,
        outputJson: result.output || null,
        status: result.success ? 'SUCCESS' : 'FAILED',
        error: result.error,
        durationMs: result.executionTimeMs,
        finishedAt: new Date(),
      },
    });

    return result.output;
  }
}
