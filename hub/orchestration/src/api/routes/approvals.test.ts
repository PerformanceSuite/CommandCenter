import { describe, it, expect, beforeEach } from 'vitest';
import request from 'supertest';
import { createServer } from '../server';
import prisma from '../../db/prisma';

describe('Approval API', () => {
  const app = createServer();

  beforeEach(async () => {
    // Clean up test data
    await prisma.workflowApproval.deleteMany();
    await prisma.agentRun.deleteMany();
    await prisma.workflowRun.deleteMany();
    await prisma.workflowNode.deleteMany();
    await prisma.workflow.deleteMany();
    await prisma.agentCapability.deleteMany();
    await prisma.agent.deleteMany();
  });

  describe('GET /api/approvals', () => {
    it('should return empty array when no approvals exist', async () => {
      const response = await request(app).get('/api/approvals');

      expect(response.status).toBe(200);
      expect(response.body).toEqual([]);
    });

    it('should filter approvals by status', async () => {
      // Create test data
      const agent = await prisma.agent.create({
        data: {
          name: 'test-agent',
          entryPath: '/agents/test',
          type: 'APPROVAL_REQUIRED',
          projectId: 'test-project',
        },
      });

      const workflow = await prisma.workflow.create({
        data: {
          name: 'test-workflow',
          projectId: 'test-project',
        },
      });

      const node = await prisma.workflowNode.create({
        data: {
          workflowId: workflow.id,
          agentId: agent.id,
          action: 'scan',
          approvalRequired: true,
        },
      });

      const workflowRun = await prisma.workflowRun.create({
        data: {
          workflowId: workflow.id,
          status: 'WAITING_APPROVAL',
          startedAt: new Date(),
        },
      });

      await prisma.workflowApproval.create({
        data: {
          workflowRunId: workflowRun.id,
          nodeId: node.id,
          status: 'PENDING',
          requestedAt: new Date(),
        },
      });

      const response = await request(app).get('/api/approvals?status=PENDING');

      expect(response.status).toBe(200);
      expect(response.body).toHaveLength(1);
      expect(response.body[0].status).toBe('PENDING');
    });
  });

  describe('POST /api/approvals/:id/decision', () => {
    it('should approve a pending approval', async () => {
      // Create test data
      const agent = await prisma.agent.create({
        data: {
          name: 'test-agent',
          entryPath: '/agents/test',
          type: 'APPROVAL_REQUIRED',
          projectId: 'test-project',
        },
      });

      const workflow = await prisma.workflow.create({
        data: {
          name: 'test-workflow',
          projectId: 'test-project',
        },
      });

      const node = await prisma.workflowNode.create({
        data: {
          workflowId: workflow.id,
          agentId: agent.id,
          action: 'scan',
          approvalRequired: true,
        },
      });

      const workflowRun = await prisma.workflowRun.create({
        data: {
          workflowId: workflow.id,
          status: 'WAITING_APPROVAL',
          startedAt: new Date(),
        },
      });

      const approval = await prisma.workflowApproval.create({
        data: {
          workflowRunId: workflowRun.id,
          nodeId: node.id,
          status: 'PENDING',
          requestedAt: new Date(),
        },
      });

      const response = await request(app)
        .post(`/api/approvals/${approval.id}/decision`)
        .send({
          decision: 'APPROVED',
          approvedBy: 'test@example.com',
        });

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('APPROVED');
      expect(response.body.approvedBy).toBe('test@example.com');
      expect(response.body.respondedAt).toBeTruthy();

      // Verify workflow status updated
      const updatedWorkflowRun = await prisma.workflowRun.findUnique({
        where: { id: workflowRun.id },
      });
      expect(updatedWorkflowRun?.status).toBe('RUNNING');
    });

    it('should reject a pending approval', async () => {
      // Create test data
      const agent = await prisma.agent.create({
        data: {
          name: 'test-agent',
          entryPath: '/agents/test',
          type: 'APPROVAL_REQUIRED',
          projectId: 'test-project',
        },
      });

      const workflow = await prisma.workflow.create({
        data: {
          name: 'test-workflow',
          projectId: 'test-project',
        },
      });

      const node = await prisma.workflowNode.create({
        data: {
          workflowId: workflow.id,
          agentId: agent.id,
          action: 'scan',
          approvalRequired: true,
        },
      });

      const workflowRun = await prisma.workflowRun.create({
        data: {
          workflowId: workflow.id,
          status: 'WAITING_APPROVAL',
          startedAt: new Date(),
        },
      });

      const approval = await prisma.workflowApproval.create({
        data: {
          workflowRunId: workflowRun.id,
          nodeId: node.id,
          status: 'PENDING',
          requestedAt: new Date(),
        },
      });

      const response = await request(app)
        .post(`/api/approvals/${approval.id}/decision`)
        .send({
          decision: 'REJECTED',
          reason: 'Too risky',
          approvedBy: 'test@example.com',
        });

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('REJECTED');
      expect(response.body.reason).toBe('Too risky');

      // Verify workflow status updated to FAILED
      const updatedWorkflowRun = await prisma.workflowRun.findUnique({
        where: { id: workflowRun.id },
      });
      expect(updatedWorkflowRun?.status).toBe('FAILED');
    });

    it('should return 400 for invalid decision', async () => {
      const approval = await prisma.workflowApproval.create({
        data: {
          workflowRunId: 'workflow-123',
          nodeId: 'node-123',
          status: 'PENDING',
          requestedAt: new Date(),
        },
      });

      const response = await request(app)
        .post(`/api/approvals/${approval.id}/decision`)
        .send({
          decision: 'INVALID',
          approvedBy: 'test@example.com',
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toContain('APPROVED or REJECTED');
    });

    it('should return 404 for non-existent approval', async () => {
      const response = await request(app)
        .post('/api/approvals/non-existent-id/decision')
        .send({
          decision: 'APPROVED',
          approvedBy: 'test@example.com',
        });

      expect(response.status).toBe(404);
    });

    it('should return 400 for already processed approval', async () => {
      const approval = await prisma.workflowApproval.create({
        data: {
          workflowRunId: 'workflow-123',
          nodeId: 'node-123',
          status: 'APPROVED',
          approvedBy: 'admin@example.com',
          requestedAt: new Date(),
          respondedAt: new Date(),
        },
      });

      const response = await request(app)
        .post(`/api/approvals/${approval.id}/decision`)
        .send({
          decision: 'APPROVED',
          approvedBy: 'test@example.com',
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toContain('already processed');
    });
  });
});
