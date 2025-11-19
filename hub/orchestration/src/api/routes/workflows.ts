import { Router } from 'express';
import prisma from '../../db/prisma';
import { WorkflowRunner } from '../../services/workflow-runner';
import daggerExecutor from '../../dagger/executor';
import natsClient from '../../events/nats-client';
import logger from '../../utils/logger';

const router = Router();
const workflowRunner = new WorkflowRunner(prisma, daggerExecutor, natsClient);

// POST /api/workflows - Create new workflow
router.post('/workflows', async (req, res) => {
  try {
    const { projectId, name, description, trigger, nodes } = req.body;

    // Validate required fields
    if (!projectId || !name || !trigger || !nodes) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['projectId', 'name', 'trigger', 'nodes'],
      });
    }

    // Check for duplicate
    const existing = await prisma.workflow.findUnique({
      where: {
        projectId_name: {
          projectId,
          name,
        },
      },
    });

    if (existing) {
      return res.status(409).json({
        error: 'Workflow with this name already exists for this project',
      });
    }

    // Create workflow with nodes
    const workflow = await prisma.workflow.create({
      data: {
        projectId,
        name,
        description,
        trigger,
        status: 'ACTIVE',
        nodes: {
          create: nodes.map((node: any) => ({
            agentId: node.agentId,
            action: node.action,
            inputsJson: node.inputsJson,
            dependsOn: node.dependsOn || [],
            approvalRequired: node.approvalRequired || false,
          })),
        },
      },
      include: {
        nodes: true,
      },
    });

    res.status(201).json(workflow);
  } catch (error: any) {
    logger.error('Failed to create workflow', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/workflows - List workflows for a project
router.get('/workflows', async (req, res) => {
  try {
    const projectId = parseInt(req.query.projectId as string);
    const status = req.query.status as string | undefined;

    if (!projectId || isNaN(projectId)) {
      return res.status(400).json({
        error: 'Missing or invalid projectId query parameter',
      });
    }

    const workflows = await prisma.workflow.findMany({
      where: {
        projectId,
        ...(status && { status: status as any }),
      },
      include: {
        nodes: true,
      },
      orderBy: { createdAt: 'desc' },
    });

    res.json(workflows);
  } catch (error: any) {
    logger.error('Failed to list workflows', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/workflows/:id - Get workflow by ID
router.get('/workflows/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const workflow = await prisma.workflow.findUnique({
      where: { id },
      include: {
        nodes: {
          include: {
            agent: true,
          },
        },
      },
    });

    if (!workflow) {
      return res.status(404).json({ error: 'Workflow not found' });
    }

    res.json(workflow);
  } catch (error: any) {
    logger.error('Failed to get workflow', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// PUT /api/workflows/:id - Update workflow
router.put('/workflows/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { description, status } = req.body;

    // Check if workflow exists
    const existing = await prisma.workflow.findUnique({
      where: { id },
    });

    if (!existing) {
      return res.status(404).json({ error: 'Workflow not found' });
    }

    const workflow = await prisma.workflow.update({
      where: { id },
      data: {
        description,
        status,
      },
      include: {
        nodes: true,
      },
    });

    res.json(workflow);
  } catch (error: any) {
    logger.error('Failed to update workflow', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// DELETE /api/workflows/:id - Delete workflow
router.delete('/workflows/:id', async (req, res) => {
  try {
    const { id } = req.params;

    // Check if workflow exists
    const existing = await prisma.workflow.findUnique({
      where: { id },
    });

    if (!existing) {
      return res.status(404).json({ error: 'Workflow not found' });
    }

    await prisma.workflow.delete({
      where: { id },
    });

    res.status(204).send();
  } catch (error: any) {
    logger.error('Failed to delete workflow', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/workflows/:id/trigger - Trigger workflow execution
router.post('/workflows/:id/trigger', async (req, res) => {
  try {
    const { id } = req.params;
    const { contextJson } = req.body;

    // Get workflow
    const workflow = await prisma.workflow.findUnique({
      where: { id },
    });

    if (!workflow) {
      return res.status(404).json({ error: 'Workflow not found' });
    }

    if (workflow.status !== 'ACTIVE') {
      return res.status(400).json({
        error: 'Cannot trigger non-active workflow',
        currentStatus: workflow.status,
      });
    }

    // Create workflow run
    const workflowRun = await prisma.workflowRun.create({
      data: {
        workflowId: id,
        trigger: 'manual',
        contextJson: contextJson || {},
        status: 'PENDING',
      },
    });

    // Execute workflow asynchronously (don't await)
    workflowRunner.executeWorkflow(workflowRun.id).catch((error) => {
      logger.error('Workflow execution failed', {
        workflowRunId: workflowRun.id,
        error,
      });
    });

    res.status(202).json({
      workflowRunId: workflowRun.id,
      status: 'PENDING',
      message: 'Workflow execution started',
    });
  } catch (error: any) {
    logger.error('Failed to trigger workflow', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/workflows/:id/runs - List workflow runs
router.get('/workflows/:id/runs', async (req, res) => {
  try {
    const { id } = req.params;

    // Verify workflow exists
    const workflow = await prisma.workflow.findUnique({
      where: { id },
    });

    if (!workflow) {
      return res.status(404).json({ error: 'Workflow not found' });
    }

    const runs = await prisma.workflowRun.findMany({
      where: { workflowId: id },
      orderBy: { startedAt: 'desc' },
      take: 50, // Limit to last 50 runs
    });

    res.json(runs);
  } catch (error: any) {
    logger.error('Failed to list workflow runs', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/workflows/:workflowId/runs/:runId - Get single workflow run with details
router.get('/workflows/:workflowId/runs/:runId', async (req, res) => {
  try {
    const { workflowId, runId } = req.params;

    const workflowRun = await prisma.workflowRun.findUnique({
      where: { id: runId },
      include: {
        workflow: {
          include: {
            nodes: {
              include: {
                agent: true,
              },
            },
          },
        },
        agentRuns: {
          include: {
            agent: true,
          },
          orderBy: { startedAt: 'asc' },
        },
        approvals: {
          orderBy: { requestedAt: 'desc' },
        },
      },
    });

    if (!workflowRun) {
      return res.status(404).json({ error: 'Workflow run not found' });
    }

    if (workflowRun.workflowId !== workflowId) {
      return res.status(400).json({
        error: 'Workflow run does not belong to specified workflow',
      });
    }

    res.json(workflowRun);
  } catch (error: any) {
    logger.error('Failed to get workflow run', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/workflows/runs/:runId/agent-runs - Get agent runs for workflow run
router.get('/workflows/runs/:runId/agent-runs', async (req, res) => {
  try {
    const { runId } = req.params;

    // Verify workflow run exists
    const workflowRun = await prisma.workflowRun.findUnique({
      where: { id: runId },
    });

    if (!workflowRun) {
      return res.status(404).json({ error: 'Workflow run not found' });
    }

    const agentRuns = await prisma.agentRun.findMany({
      where: { workflowRunId: runId },
      include: {
        agent: {
          include: {
            capabilities: true,
          },
        },
      },
      orderBy: { startedAt: 'asc' },
    });

    res.json(agentRuns);
  } catch (error: any) {
    logger.error('Failed to list agent runs', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/workflows/runs/:runId/retry - Retry failed workflow run
router.post('/workflows/runs/:runId/retry', async (req, res) => {
  try {
    const { runId } = req.params;

    // Get original workflow run
    const originalRun = await prisma.workflowRun.findUnique({
      where: { id: runId },
      include: {
        workflow: true,
      },
    });

    if (!originalRun) {
      return res.status(404).json({ error: 'Workflow run not found' });
    }

    if (originalRun.status !== 'FAILED') {
      return res.status(400).json({
        error: 'Can only retry failed workflow runs',
        currentStatus: originalRun.status,
      });
    }

    // Create new workflow run with same context
    const newRun = await prisma.workflowRun.create({
      data: {
        workflowId: originalRun.workflowId,
        trigger: 'retry',
        contextJson: originalRun.contextJson,
        status: 'PENDING',
      },
    });

    // Execute workflow asynchronously
    workflowRunner.executeWorkflow(newRun.id).catch((error) => {
      logger.error('Workflow retry execution failed', {
        workflowRunId: newRun.id,
        originalRunId: runId,
        error,
      });
    });

    res.status(202).json({
      workflowRunId: newRun.id,
      originalRunId: runId,
      status: 'PENDING',
      message: 'Workflow retry started',
    });
  } catch (error: any) {
    logger.error('Failed to retry workflow', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
