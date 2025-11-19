import { Router } from 'express';
import prisma from '../../db/prisma';
import logger from '../../utils/logger';

const router = Router();

// GET /api/approvals?status=PENDING&workflowRunId=xxx
router.get('/approvals', async (req, res) => {
  try {
    const { status, workflowRunId } = req.query;

    const approvals = await prisma.workflowApproval.findMany({
      where: {
        ...(status && { status: status as string }),
        ...(workflowRunId && { workflowRunId: workflowRunId as string }),
      },
      include: {
        workflowRun: {
          include: {
            workflow: true,
          },
        },
        node: {
          include: {
            agent: true,
          },
        },
      },
      orderBy: { requestedAt: 'desc' },
    });

    res.json(approvals);
  } catch (error: any) {
    logger.error('Failed to fetch approvals', { error });
    res.status(500).json({ error: 'Failed to fetch approvals' });
  }
});

// POST /api/approvals/:id/decision
router.post('/approvals/:id/decision', async (req, res) => {
  try {
    const { id } = req.params;
    const { decision, notes, respondedBy } = req.body;

    // Validate decision
    if (!['APPROVED', 'REJECTED'].includes(decision)) {
      return res
        .status(400)
        .json({ error: 'Decision must be APPROVED or REJECTED' });
    }

    // Validate respondedBy
    if (!respondedBy || typeof respondedBy !== 'string') {
      return res.status(400).json({ error: 'respondedBy is required' });
    }

    // Find approval
    const approval = await prisma.workflowApproval.findUnique({
      where: { id },
    });

    if (!approval) {
      return res.status(404).json({ error: 'Approval not found' });
    }

    if (approval.status !== 'PENDING') {
      return res.status(400).json({
        error: 'Approval already processed',
        status: approval.status,
      });
    }

    // Update approval
    const updated = await prisma.workflowApproval.update({
      where: { id },
      data: {
        status: decision,
        respondedBy,
        notes,
        respondedAt: new Date(),
      },
    });

    logger.info('Approval decision recorded', {
      approvalId: id,
      decision,
      respondedBy,
    });

    // Resume workflow if approved
    if (decision === 'APPROVED') {
      await prisma.workflowRun.update({
        where: { id: approval.workflowRunId },
        data: { status: 'RUNNING' },
      });
      logger.info('Workflow resumed after approval', {
        workflowRunId: approval.workflowRunId,
      });
    } else {
      // Mark workflow as failed if rejected
      await prisma.workflowRun.update({
        where: { id: approval.workflowRunId },
        data: {
          status: 'FAILED',
          finishedAt: new Date(),
        },
      });
      logger.info('Workflow failed due to rejection', {
        workflowRunId: approval.workflowRunId,
        notes,
      });
    }

    res.json(updated);
  } catch (error: any) {
    logger.error('Failed to process approval decision', { error });
    res.status(500).json({ error: 'Failed to process approval decision' });
  }
});

export default router;
