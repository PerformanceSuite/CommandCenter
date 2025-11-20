// hub/orchestration/src/api/routes/webhooks.ts
// Webhook endpoints for external integrations (AlertManager, Grafana, etc.)

import { Router, Request, Response } from 'express';
import prisma from '../../db/prisma';
import { WorkflowRunner } from '../../services/workflow-runner';
import daggerExecutor from '../../dagger/executor';
import natsClient from '../../events/nats-client';
import logger from '../../utils/logger';

const router = Router();
const workflowRunner = new WorkflowRunner(prisma, daggerExecutor, natsClient);

/**
 * AlertManager Webhook - Receives alerts from Prometheus AlertManager
 * Triggers the alert-notification workflow with notifier agent
 */
router.post('/alertmanager', async (req: Request, res: Response) => {
  try {
    const alertmanagerPayload = req.body;

    // AlertManager sends multiple alerts in a single webhook
    const alerts = alertmanagerPayload.alerts || [];

    if (alerts.length === 0) {
      return res.status(200).json({ message: 'No alerts to process' });
    }

    // Find or create the alert-notification workflow
    let workflow = await prisma.workflow.findFirst({
      where: { name: 'alert-notification' },
    });

    if (!workflow) {
      // Find the notifier agent
      const notifier = await prisma.agent.findFirst({
        where: { name: 'notifier' },
      });

      if (!notifier) {
        logger.error('Notifier agent not found - cannot create alert-notification workflow');
        return res.status(500).json({
          error: 'Notifier agent not registered',
        });
      }

      // Create the alert-notification workflow if it doesn't exist
      workflow = await prisma.workflow.create({
        data: {
          projectId: 1, // Default project
          name: 'alert-notification',
          description: 'Send alert notifications via Slack/Discord',
          trigger: 'webhook',
          status: 'ACTIVE',
          nodes: {
            create: [
              {
                agentId: notifier.id,
                action: 'notify',
                inputsJson: {
                  channel: '{{ context.channel }}',
                  message: '{{ context.message }}',
                  severity: '{{ context.severity }}',
                },
                dependsOn: [],
                approvalRequired: false,
              },
            ],
          },
        },
      });
    }

    // Process each alert
    const workflowRuns = [];
    for (const alert of alerts) {
      const { status, labels, annotations } = alert;

      // Map AlertManager severity to notifier severity
      const severity = labels.severity || 'warning';

      // Build notification message
      const message = buildAlertMessage(alert);

      // Determine notification channel based on severity
      const channel = severity === 'critical' ? 'slack' : 'console';

      // Create workflow run
      const workflowRun = await prisma.workflowRun.create({
        data: {
          workflowId: workflow.id,
          trigger: 'alertmanager_webhook',
          contextJson: {
            status,
            severity,
            channel,
            message,
            alert_name: labels.alertname,
            component: labels.component,
            dashboard_url: annotations.dashboard_url,
            runbook_url: annotations.runbook_url,
            timestamp: new Date().toISOString(),
            labels,
            annotations,
          },
          status: 'PENDING',
        },
      });

      workflowRuns.push(workflowRun);

      // Execute workflow asynchronously (don't await to avoid blocking)
      workflowRunner.executeWorkflow(workflowRun.id).catch(async (err) => {
        logger.error('Alert workflow execution failed', {
          workflowRunId: workflowRun.id,
          error: err,
        });

        // Update workflow run status to FAILED
        await prisma.workflowRun.update({
          where: { id: workflowRun.id },
          data: {
            status: 'FAILED',
            finishedAt: new Date(),
          },
        });
      });
    }

    res.status(200).json({
      message: `Processed ${alerts.length} alerts`,
      workflowRuns: workflowRuns.map((run) => ({
        id: run.id,
        status: run.status,
      })),
    });
  } catch (error) {
    logger.error('Error processing AlertManager webhook:', { error });
    res.status(500).json({
      error: 'Failed to process AlertManager webhook',
      details: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Build formatted alert message for notification
 */
function buildAlertMessage(alert: any): string {
  const { status, labels, annotations } = alert;
  const severity = labels.severity || 'warning';
  const alertName = labels.alertname || 'Unknown Alert';
  const component = labels.component || 'unknown';
  const summary = annotations.summary || 'No summary available';
  const description = annotations.description || '';
  const runbookUrl = annotations.runbook_url || '';

  // Emoji mapping for severity
  const emojiMap: Record<string, string> = {
    critical: '🔴',
    warning: '⚠️',
    info: 'ℹ️',
  };
  const emoji = emojiMap[severity] || '📢';

  // Status emoji
  const statusEmoji = status === 'firing' ? '🔥' : '✅';

  let message = `${statusEmoji} ${emoji} **${alertName}**\n`;
  message += `**Status:** ${status}\n`;
  message += `**Severity:** ${severity}\n`;
  message += `**Component:** ${component}\n`;
  message += `**Summary:** ${summary}\n`;

  if (description) {
    message += `**Description:** ${description}\n`;
  }

  if (runbookUrl) {
    message += `**Runbook:** ${runbookUrl}\n`;
  }

  return message;
}

/**
 * Grafana Webhook - Receives alerts from Grafana (alternative to AlertManager)
 * Supports Grafana's native alerting system
 */
router.post('/grafana', async (req: Request, res: Response) => {
  try {
    const grafanaAlert = req.body;

    // Map Grafana alert to workflow context
    const context = {
      severity: grafanaAlert.state === 'alerting' ? 'critical' : 'warning',
      alert_name: grafanaAlert.ruleName,
      message: grafanaAlert.message,
      dashboard_url: grafanaAlert.dashboardURL,
      timestamp: new Date().toISOString(),
      labels: grafanaAlert.labels || {},
    };

    // Find alert-notification workflow
    const workflow = await prisma.workflow.findFirst({
      where: { name: 'alert-notification' },
    });

    if (!workflow) {
      return res.status(404).json({ error: 'Alert workflow not found' });
    }

    // Create workflow run
    const workflowRun = await prisma.workflowRun.create({
      data: {
        workflowId: workflow.id,
        trigger: 'grafana_webhook',
        contextJson: context,
        status: 'PENDING',
      },
    });

    // Execute workflow
    workflowRunner.executeWorkflow(workflowRun.id).catch(async (err) => {
      logger.error('Grafana alert workflow execution failed', {
        workflowRunId: workflowRun.id,
        error: err,
      });

      // Update workflow run status to FAILED
      await prisma.workflowRun.update({
        where: { id: workflowRun.id },
        data: {
          status: 'FAILED',
          finishedAt: new Date(),
        },
      });
    });

    res.status(200).json({ workflowRunId: workflowRun.id });
  } catch (error) {
    logger.error('Error processing Grafana webhook:', { error });
    res.status(500).json({
      error: 'Failed to process Grafana webhook',
      details: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

export default router;
