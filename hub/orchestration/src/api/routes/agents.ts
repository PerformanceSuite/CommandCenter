import { Router } from 'express';
import { AgentRegistry } from '../../services/agent-registry';
import prisma from '../../db/prisma';
import logger from '../../utils/logger';

const router = Router();
const agentRegistry = new AgentRegistry(prisma);

// POST /api/agents - Register new agent
router.post('/agents', async (req, res) => {
  try {
    const { projectId, name, type, description, entryPath, version, riskLevel, capabilities } = req.body;

    // Validate required fields
    if (!projectId || !name || !type || !entryPath || !version || !riskLevel) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['projectId', 'name', 'type', 'entryPath', 'version', 'riskLevel'],
      });
    }

    // Validate enums
    const validTypes = ['LLM', 'RULE', 'API', 'SCRIPT'];
    const validRiskLevels = ['AUTO', 'APPROVAL_REQUIRED'];

    if (!validTypes.includes(type)) {
      return res.status(400).json({
        error: 'Invalid type',
        validTypes,
      });
    }

    if (!validRiskLevels.includes(riskLevel)) {
      return res.status(400).json({
        error: 'Invalid riskLevel',
        validRiskLevels,
      });
    }

    // Check for duplicate
    const existing = await prisma.agent.findUnique({
      where: {
        projectId_name: {
          projectId,
          name,
        },
      },
    });

    if (existing) {
      return res.status(409).json({
        error: 'Agent with this name already exists for this project',
      });
    }

    const agent = await agentRegistry.register({
      projectId,
      name,
      type,
      description,
      entryPath,
      version,
      riskLevel,
      capabilities: capabilities || [],
    });

    res.status(201).json(agent);
  } catch (error: any) {
    logger.error('Failed to register agent', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/agents - List agents for a project
router.get('/agents', async (req, res) => {
  try {
    const projectId = parseInt(req.query.projectId as string);

    if (!projectId || isNaN(projectId)) {
      return res.status(400).json({
        error: 'Missing or invalid projectId query parameter',
      });
    }

    const agents = await agentRegistry.listByProject(projectId);
    res.json(agents);
  } catch (error: any) {
    logger.error('Failed to list agents', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/agents/:id - Get agent by ID
router.get('/agents/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const agent = await agentRegistry.getById(id);

    if (!agent) {
      return res.status(404).json({ error: 'Agent not found' });
    }

    res.json(agent);
  } catch (error: any) {
    logger.error('Failed to get agent', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// PUT /api/agents/:id - Update agent
router.put('/agents/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    // Check if agent exists
    const existing = await agentRegistry.getById(id);
    if (!existing) {
      return res.status(404).json({ error: 'Agent not found' });
    }

    const agent = await agentRegistry.update(id, updateData);
    res.json(agent);
  } catch (error: any) {
    logger.error('Failed to update agent', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// DELETE /api/agents/:id - Delete agent
router.delete('/agents/:id', async (req, res) => {
  try {
    const { id } = req.params;

    // Check if agent exists
    const existing = await agentRegistry.getById(id);
    if (!existing) {
      return res.status(404).json({ error: 'Agent not found' });
    }

    await agentRegistry.delete(id);
    res.status(204).send();
  } catch (error: any) {
    logger.error('Failed to delete agent', { error });
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
