import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import request from 'supertest';
import { createServer } from '../server';
import prisma from '../../db/prisma';

describe('Agent API Endpoints', () => {
  const app = createServer();

  beforeEach(async () => {
    // Clean up test data
    await prisma.agent.deleteMany({});
  });

  afterEach(async () => {
    // Clean up after tests
    await prisma.agent.deleteMany({});
  });

  describe('POST /api/agents', () => {
    it('should register a new agent', async () => {
      const agentData = {
        projectId: 1,
        name: 'test-agent',
        type: 'SCRIPT',
        description: 'Test agent',
        entryPath: 'agents/test.ts',
        version: '1.0.0',
        riskLevel: 'AUTO',
        capabilities: [
          {
            name: 'testAction',
            description: 'Test action',
            inputSchema: { type: 'object' },
            outputSchema: { type: 'object' },
          },
        ],
      };

      const response = await request(app)
        .post('/api/agents')
        .send(agentData)
        .expect(201);

      expect(response.body.id).toBeDefined();
      expect(response.body.name).toBe('test-agent');
      expect(response.body.capabilities).toHaveLength(1);
    });

    it('should reject agent with missing required fields', async () => {
      const invalidData = {
        projectId: 1,
        name: 'test-agent',
        // missing type, entryPath, version, riskLevel
      };

      await request(app).post('/api/agents').send(invalidData).expect(400);
    });

    it('should reject duplicate agent name for same project', async () => {
      const agentData = {
        projectId: 1,
        name: 'duplicate-agent',
        type: 'SCRIPT',
        entryPath: 'agents/dup.ts',
        version: '1.0.0',
        riskLevel: 'AUTO',
        capabilities: [],
      };

      // Create first agent
      await request(app).post('/api/agents').send(agentData).expect(201);

      // Attempt to create duplicate
      await request(app).post('/api/agents').send(agentData).expect(409);
    });
  });

  describe('GET /api/agents', () => {
    beforeEach(async () => {
      // Create test agents
      await prisma.agent.createMany({
        data: [
          {
            projectId: 1,
            name: 'agent1',
            type: 'SCRIPT',
            entryPath: 'agents/agent1.ts',
            version: '1.0.0',
            riskLevel: 'AUTO',
          },
          {
            projectId: 1,
            name: 'agent2',
            type: 'LLM',
            entryPath: 'agents/agent2.ts',
            version: '1.0.0',
            riskLevel: 'APPROVAL_REQUIRED',
          },
          {
            projectId: 2,
            name: 'agent3',
            type: 'API',
            entryPath: 'agents/agent3.ts',
            version: '1.0.0',
            riskLevel: 'AUTO',
          },
        ],
      });
    });

    it('should list all agents for a project', async () => {
      const response = await request(app)
        .get('/api/agents?projectId=1')
        .expect(200);

      expect(response.body).toHaveLength(2);
      expect(response.body[0].name).toBe('agent1');
      expect(response.body[1].name).toBe('agent2');
    });

    it('should require projectId query parameter', async () => {
      await request(app).get('/api/agents').expect(400);
    });
  });

  describe('GET /api/agents/:id', () => {
    it('should get agent by id', async () => {
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

      const response = await request(app)
        .get(`/api/agents/${agent.id}`)
        .expect(200);

      expect(response.body.id).toBe(agent.id);
      expect(response.body.name).toBe('test-agent');
    });

    it('should return 404 for non-existent agent', async () => {
      await request(app).get('/api/agents/nonexistent-id').expect(404);
    });
  });

  describe('PUT /api/agents/:id', () => {
    it('should update agent', async () => {
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

      const updateData = {
        description: 'Updated description',
        version: '1.1.0',
      };

      const response = await request(app)
        .put(`/api/agents/${agent.id}`)
        .send(updateData)
        .expect(200);

      expect(response.body.description).toBe('Updated description');
      expect(response.body.version).toBe('1.1.0');
    });
  });

  describe('DELETE /api/agents/:id', () => {
    it('should delete agent', async () => {
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

      await request(app).delete(`/api/agents/${agent.id}`).expect(204);

      // Verify deletion
      const deleted = await prisma.agent.findUnique({
        where: { id: agent.id },
      });
      expect(deleted).toBeNull();
    });

    it('should return 404 for non-existent agent', async () => {
      await request(app).delete('/api/agents/nonexistent-id').expect(404);
    });
  });
});
