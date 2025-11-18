import { PrismaClient, Workflow } from '@prisma/client';
import { NatsClient } from '../events/nats-client';
import { WorkflowRunner } from './workflow-runner';
import logger from '../utils/logger';

export interface NatsEvent {
  type: string;
  payload: Record<string, unknown>;
  timestamp?: string;
  source?: string;
}

export class EventBridge {
  private workflowRunner: WorkflowRunner | null = null;

  constructor(
    private prisma: PrismaClient,
    private natsClient: NatsClient
  ) {}

  setWorkflowRunner(runner: WorkflowRunner): void {
    this.workflowRunner = runner;
  }

  async start(): Promise<void> {
    // Subscribe to workflow trigger events
    await this.natsClient.subscribe('workflow.trigger.*', async (data) => {
      const event = data as NatsEvent;
      logger.info('Received workflow trigger event', { type: event.type });
      await this.handleEvent(event);
    });

    // Subscribe to graph events
    await this.natsClient.subscribe('graph.*', async (data) => {
      const event = data as NatsEvent;
      logger.info('Received graph event', { type: event.type });
      await this.handleEvent(event);
    });

    // Subscribe to health events
    await this.natsClient.subscribe('health.*', async (data) => {
      const event = data as NatsEvent;
      logger.info('Received health event', { type: event.type });
      await this.handleEvent(event);
    });

    logger.info('Event bridge started - listening for NATS events');
  }

  /**
   * Handle incoming NATS event and trigger matching workflows
   */
  private async handleEvent(event: NatsEvent): Promise<void> {
    try {
      // Find workflows that match this event
      const matchedWorkflows = await this.matchWorkflows(event);

      if (matchedWorkflows.length === 0) {
        logger.debug('No workflows matched event', { eventType: event.type });
        return;
      }

      logger.info('Matched workflows', {
        eventType: event.type,
        count: matchedWorkflows.length,
      });

      // Create workflow runs for each matched workflow
      for (const workflow of matchedWorkflows) {
        await this.triggerWorkflow(workflow, event);
      }
    } catch (error) {
      logger.error('Failed to handle event', { event, error });
    }
  }

  /**
   * Find workflows that match the event pattern
   */
  private async matchWorkflows(event: NatsEvent): Promise<Workflow[]> {
    // Get all active workflows with event triggers
    const workflows = await this.prisma.workflow.findMany({
      where: {
        status: 'ACTIVE',
      },
    });

    // Filter workflows that match the event pattern
    return workflows.filter((workflow) => {
      const trigger = workflow.trigger as any;

      if (trigger.type !== 'event') {
        return false;
      }

      const pattern = trigger.pattern as string;
      return this.patternMatches(event.type, pattern);
    });
  }

  /**
   * Check if event type matches pattern (supports wildcards)
   */
  private patternMatches(eventType: string, pattern: string): boolean {
    // Exact match
    if (eventType === pattern) {
      return true;
    }

    // Convert pattern to regex
    // '*' matches single segment
    // '>' matches multiple segments (must be at end)

    let regexPattern = pattern
      .replace(/\./g, '\\.') // Escape dots
      .replace(/\*/g, '[^.]+') // * matches one segment
      .replace(/>/g, '.*'); // > matches multiple segments

    regexPattern = `^${regexPattern}$`;

    const regex = new RegExp(regexPattern);
    return regex.test(eventType);
  }

  /**
   * Trigger workflow execution for an event
   */
  private async triggerWorkflow(
    workflow: Workflow,
    event: NatsEvent
  ): Promise<void> {
    try {
      // Create workflow run
      const workflowRun = await this.prisma.workflowRun.create({
        data: {
          workflowId: workflow.id,
          trigger: `event:${event.type}`,
          contextJson: {
            event: event.payload,
            timestamp: event.timestamp || new Date().toISOString(),
            source: event.source || 'nats-bridge',
          } as any,
          status: 'PENDING',
        },
      });

      logger.info('Created workflow run from event', {
        workflowId: workflow.id,
        workflowName: workflow.name,
        workflowRunId: workflowRun.id,
        eventType: event.type,
      });

      // Execute workflow asynchronously
      if (this.workflowRunner) {
        this.workflowRunner.executeWorkflow(workflowRun.id).catch((error) => {
          logger.error('Workflow execution failed', {
            workflowRunId: workflowRun.id,
            error,
          });
        });
      } else {
        logger.warn('WorkflowRunner not set, workflow will not execute', {
          workflowRunId: workflowRun.id,
        });
      }
    } catch (error) {
      logger.error('Failed to trigger workflow', {
        workflowId: workflow.id,
        event,
        error,
      });
    }
  }
}

export default EventBridge;
