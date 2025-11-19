import { PrismaClient, WorkflowNode } from '@prisma/client';
import { DaggerAgentExecutor } from '../dagger/executor';
import { NatsClient } from '../events/nats-client';
import logger from '../utils/logger';

export class WorkflowRunner {
  constructor(
    private prisma: PrismaClient,
    private daggerExecutor: DaggerAgentExecutor,
    private natsClient: NatsClient
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

  /**
   * Check if approval is required and wait for decision
   */
  private async checkApprovalIfNeeded(
    node: WorkflowNode & { agent: any },
    workflowRunId: string
  ): Promise<void> {
    if (!node.approvalRequired) return;

    logger.info('Approval required for node', {
      nodeId: node.id,
      agentName: node.agent.name,
    });

    // Create approval request
    const approval = await this.prisma.workflowApproval.create({
      data: {
        workflowRunId,
        nodeId: node.id,
        status: 'PENDING',
        requestedAt: new Date(),
      },
    });

    // Update workflow status to WAITING_APPROVAL
    await this.prisma.workflowRun.update({
      where: { id: workflowRunId },
      data: { status: 'WAITING_APPROVAL' },
    });

    // Publish NATS event for UI notification
    await this.natsClient.publish('workflow.approval.requested', {
      approvalId: approval.id,
      workflowRunId,
      nodeId: node.id,
      agentName: node.agent.name,
      action: node.action,
      inputsPreview: JSON.stringify(node.inputsJson, null, 2),
    });

    logger.info('Approval request created', {
      approvalId: approval.id,
      workflowRunId,
    });

    // Wait for approval decision
    await this.waitForApproval(approval.id);
  }

  /**
   * Wait for approval decision with 24-hour timeout
   */
  private async waitForApproval(approvalId: string): Promise<void> {
    const maxWaitMs = 24 * 60 * 60 * 1000; // 24 hours
    const pollIntervalMs = 5000; // 5 seconds
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitMs) {
      const approval = await this.prisma.workflowApproval.findUnique({
        where: { id: approvalId },
      });

      if (!approval) {
        throw new Error(`Approval ${approvalId} not found`);
      }

      if (approval.status === 'APPROVED') {
        logger.info('Approval granted', {
          approvalId,
          approvedBy: approval.approvedBy,
          approvedAt: approval.respondedAt,
        });
        return;
      }

      if (approval.status === 'REJECTED') {
        logger.warn('Approval rejected', {
          approvalId,
          rejectedBy: approval.approvedBy,
          reason: approval.reason,
        });
        throw new Error(
          `Workflow node rejected: ${approval.reason || 'No reason provided'}`
        );
      }

      await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
    }

    // Timeout - auto-reject
    await this.prisma.workflowApproval.update({
      where: { id: approvalId },
      data: {
        status: 'REJECTED',
        reason: 'Approval timeout after 24 hours',
        respondedAt: new Date(),
      },
    });

    throw new Error(`Approval timeout after ${maxWaitMs}ms`);
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

    // 🔒 APPROVAL GATE: Check if approval is required before execution
    await this.checkApprovalIfNeeded(node, workflowRun.id);

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
