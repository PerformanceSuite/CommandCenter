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
  private topologicalSort<T extends WorkflowNode>(nodes: T[]): T[][] {
    const batches: T[][] = [];
    const remaining = new Set(nodes);
    const completed = new Set<string>();

    while (remaining.size > 0) {
      // Find nodes with all dependencies satisfied
      const batch: T[] = [];

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

    // Initialize context and output tracking for template resolution
    const context = (workflowRun.contextJson as Record<string, any>) || {};
    const previousOutputs = new Map<string, any>();

    const dag = this.topologicalSort(workflowRun.workflow.nodes);

    logger.info('Executing workflow', {
      workflowRunId,
      workflowName: workflowRun.workflow.name,
      batches: dag.length,
      context,
    });

    // Execute batches sequentially, nodes in batch in parallel
    for (const batch of dag) {
      await Promise.all(
        batch.map(async node => {
          const output = await this.executeNode(
            node,
            workflowRun,
            context,
            previousOutputs
          );
          // Store output for downstream nodes
          previousOutputs.set(node.id, output);
        })
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

  /**
   * Resolve template variables in node inputs
   * Supports: {{ context.* }} and {{ nodes.*.output.* }}
   */
  private resolveInputs(
    node: WorkflowNode,
    context: Record<string, any>,
    previousOutputs: Map<string, any>
  ): any {
    const templateString = JSON.stringify(node.inputsJson);

    logger.debug('Resolving input templates', {
      nodeId: node.id,
      template: templateString,
    });

    // Replace {{ context.* }} and {{ nodes.*.output.* }}
    const resolved = templateString.replace(
      /\{\{\s*(context|nodes)\.([^}]+)\s*\}\}/g,
      (match, source, path) => {
        if (source === 'context') {
          const value = this.getNestedValue(context, path);
          if (value !== undefined) {
            return JSON.stringify(value);
          }
        } else if (source === 'nodes') {
          // Convert previousOutputs Map to object for getNestedValue
          const outputsObj: Record<string, any> = {};
          previousOutputs.forEach((value, key) => {
            outputsObj[key] = { output: value };
          });

          const value = this.getNestedValue(outputsObj, path);
          if (value !== undefined) {
            return JSON.stringify(value);
          }
        }

        // If value not found, keep original template
        logger.warn('Template variable not found', {
          nodeId: node.id,
          template: match,
          source,
          path,
        });
        return match;
      }
    );

    try {
      const result = JSON.parse(resolved);
      logger.debug('Input templates resolved', {
        nodeId: node.id,
        resolved: result,
      });
      return result;
    } catch (error: any) {
      logger.error('Failed to parse resolved template', {
        nodeId: node.id,
        template: templateString,
        resolved,
        error,
      });
      throw new Error(`Template resolution failed: ${error.message}`);
    }
  }

  /**
   * Get nested value from object using dot notation path
   */
  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => {
      if (current === undefined || current === null) return undefined;
      return current[key];
    }, obj);
  }

  private async executeNode(
    node: WorkflowNode & { agent: any },
    workflowRun: any,
    context: Record<string, any>,
    previousOutputs: Map<string, any>
  ): Promise<unknown> {
    logger.info('Executing workflow node', {
      nodeId: node.id,
      agentName: node.agent.name,
    });

    // ✅ Resolve inputs from template
    const inputs = this.resolveInputs(node, context, previousOutputs);

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
        inputJson: inputs as any,
        outputJson: (result.output as any) || null,
        status: result.success ? 'SUCCESS' : 'FAILED',
        error: result.error || null,
        durationMs: result.executionTimeMs,
        finishedAt: new Date(),
      },
    });

    return result.output;
  }
}
