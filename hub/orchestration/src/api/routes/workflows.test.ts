import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import request from 'supertest';
import { createServer } from '../server';
import prisma from '../../db/prisma';

describe('Workflow API Endpoints', () => {
  const app = createServer();
  let testAgentId: string;

  beforeEach(async () => {
    // Clean up test data
    await prisma.workflowRun.deleteMany({});
    await prisma.workflowNode.deleteMany({});
    await prisma.workflow.deleteMany({});
    await prisma.agentRun.deleteMany({});
    await prisma.agentCapability.deleteMany({});
    await prisma.agent.deleteMany({});

    // Create test agent
    const agent = await prisma.agent.create({
      data: {
        projectId: 1,
        name: 'test-agent',
        type: 'SCRIPT',
        entryPath: 'agents/test.ts',
        version: '1.0.0',
        riskLevel: 'AUTO',
      },
    });
    testAgentId = agent.id;
  });

  afterEach(async () => {
    // Clean up after tests
    await prisma.workflowRun.deleteMany({});
    await prisma.workflowNode.deleteMany({});
    await prisma.workflow.deleteMany({});
    await prisma.agentRun.deleteMany({});
    await prisma.agentCapability.deleteMany({});
    await prisma.agent.deleteMany({});
  });

  describe('POST /api/workflows', () => {
    it('should create a new workflow', async () => {
      const workflowData = {
        projectId: 1,
        name: 'test-workflow',
        description: 'Test workflow',
        trigger: {
          type: 'event',
          pattern: 'graph.file.updated',
        },
        nodes: [
          {
            agentId: testAgentId,
            action: 'scan',
            inputsJson: { path: '{{event.file_path}}' },
            dependsOn: [],
            approvalRequired: false,
          },
        ],
      };

      const response = await request(app)
        .post('/api/workflows')
        .send(workflowData)
        .expect(201);

      expect(response.body.id).toBeDefined();
      expect(response.body.name).toBe('test-workflow');
      expect(response.body.nodes).toHaveLength(1);
      expect(response.body.status).toBe('ACTIVE');
    });

    it('should reject workflow with missing required fields', async () => {
      const invalidData = {
        projectId: 1,
        // missing name, trigger, nodes
      };

      await request(app).post('/api/workflows').send(invalidData).expect(400);
    });

    it('should reject duplicate workflow name for same project', async () => {
      const workflowData = {
        projectId: 1,
        name: 'duplicate-workflow',
        trigger: { type: 'manual' },
        nodes: [],
      };

      // Create first workflow
      await request(app).post('/api/workflows').send(workflowData).expect(201);

      // Attempt to create duplicate
      await request(app).post('/api/workflows').send(workflowData).expect(409);
    });
  });

  describe('GET /api/workflows', () => {
    beforeEach(async () => {
      // Create test workflows
      await prisma.workflow.createMany({
        data: [
          {
            projectId: 1,
            name: 'workflow1',
            trigger: { type: 'event' },
            status: 'ACTIVE',
          },
          {
            projectId: 1,
            name: 'workflow2',
            trigger: { type: 'schedule' },
            status: 'DRAFT',
          },
          {
            projectId: 2,
            name: 'workflow3',
            trigger: { type: 'manual' },
            status: 'ACTIVE',
          },
        ],
      });
    });

    it('should list all workflows for a project', async () => {
      const response = await request(app)
        .get('/api/workflows?projectId=1')
        .expect(200);

      expect(response.body).toHaveLength(2);
      expect(response.body[0].name).toBe('workflow1');
    });

    it('should filter workflows by status', async () => {
      const response = await request(app)
        .get('/api/workflows?projectId=1&status=ACTIVE')
        .expect(200);

      expect(response.body).toHaveLength(1);
      expect(response.body[0].status).toBe('ACTIVE');
    });

    it('should require projectId query parameter', async () => {
      await request(app).get('/api/workflows').expect(400);
    });
  });

  describe('GET /api/workflows/:id', () => {
    it('should get workflow by id with nodes', async () => {
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'test-workflow',
          trigger: { type: 'manual' },
          status: 'ACTIVE',
          nodes: {
            create: [
              {
                agentId: testAgentId,
                action: 'scan',
                inputsJson: {},
                dependsOn: [],
                approvalRequired: false,
              },
            ],
          },
        },
      });

      const response = await request(app)
        .get(`/api/workflows/${workflow.id}`)
        .expect(200);

      expect(response.body.id).toBe(workflow.id);
      expect(response.body.nodes).toHaveLength(1);
    });

    it('should return 404 for non-existent workflow', async () => {
      await request(app).get('/api/workflows/nonexistent-id').expect(404);
    });
  });

  describe('PUT /api/workflows/:id', () => {
    it('should update workflow', async () => {
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'test-workflow',
          trigger: { type: 'manual' },
          status: 'DRAFT',
        },
      });

      const updateData = {
        description: 'Updated description',
        status: 'ACTIVE',
      };

      const response = await request(app)
        .put(`/api/workflows/${workflow.id}`)
        .send(updateData)
        .expect(200);

      expect(response.body.description).toBe('Updated description');
      expect(response.body.status).toBe('ACTIVE');
    });
  });

  describe('DELETE /api/workflows/:id', () => {
    it('should delete workflow', async () => {
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'test-workflow',
          trigger: { type: 'manual' },
          status: 'DRAFT',
        },
      });

      await request(app).delete(`/api/workflows/${workflow.id}`).expect(204);

      // Verify deletion
      const deleted = await prisma.workflow.findUnique({
        where: { id: workflow.id },
      });
      expect(deleted).toBeNull();
    });
  });

  describe('POST /api/workflows/:id/trigger', () => {
    it('should trigger workflow execution', async () => {
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'test-workflow',
          trigger: { type: 'manual' },
          status: 'ACTIVE',
          nodes: {
            create: [
              {
                agentId: testAgentId,
                action: 'scan',
                inputsJson: {},
                dependsOn: [],
                approvalRequired: false,
              },
            ],
          },
        },
      });

      const triggerData = {
        contextJson: {
          triggeredBy: 'user',
          timestamp: new Date().toISOString(),
        },
      };

      const response = await request(app)
        .post(`/api/workflows/${workflow.id}/trigger`)
        .send(triggerData)
        .expect(202);

      expect(response.body.workflowRunId).toBeDefined();
      expect(response.body.status).toBe('PENDING');

      // Verify workflow run was created
      const workflowRun = await prisma.workflowRun.findUnique({
        where: { id: response.body.workflowRunId },
      });
      expect(workflowRun).toBeDefined();
      expect(workflowRun?.status).toBe('PENDING');
    });

    it('should reject trigger for non-active workflow', async () => {
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'test-workflow',
          trigger: { type: 'manual' },
          status: 'DRAFT',
        },
      });

      await request(app)
        .post(`/api/workflows/${workflow.id}/trigger`)
        .send({ contextJson: {} })
        .expect(400);
    });
  });

  describe('GET /api/workflows/:id/runs', () => {
    it('should list workflow runs', async () => {
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'test-workflow',
          trigger: { type: 'manual' },
          status: 'ACTIVE',
        },
      });

      // Create test runs
      await prisma.workflowRun.createMany({
        data: [
          {
            workflowId: workflow.id,
            trigger: 'manual',
            contextJson: {},
            status: 'SUCCESS',
            finishedAt: new Date(),
          },
          {
            workflowId: workflow.id,
            trigger: 'manual',
            contextJson: {},
            status: 'FAILED',
            finishedAt: new Date(),
          },
        ],
      });

      const response = await request(app)
        .get(`/api/workflows/${workflow.id}/runs`)
        .expect(200);

      expect(response.body).toHaveLength(2);
      expect(response.body[0].status).toBeDefined();
    });
  });
});
