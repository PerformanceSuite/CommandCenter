import { PrismaClient, Agent, AgentType, RiskLevel } from '@prisma/client';
import logger from '../utils/logger';

export interface RegisterAgentInput {
  projectId: number;
  name: string;
  type: AgentType;
  description?: string;
  entryPath: string;
  version: string;
  riskLevel: RiskLevel;
  capabilities: Array<{
    name: string;
    description?: string;
    inputSchema: object;
    outputSchema: object;
  }>;
}

export class AgentRegistry {
  constructor(private prisma: PrismaClient) {}

  async register(input: RegisterAgentInput): Promise<Agent> {
    const agent = await this.prisma.agent.create({
      data: {
        projectId: input.projectId,
        name: input.name,
        type: input.type,
        description: input.description,
        entryPath: input.entryPath,
        version: input.version,
        riskLevel: input.riskLevel,
        capabilities: {
          create: input.capabilities,
        },
      },
      include: {
        capabilities: true,
      },
    });

    logger.info('Agent registered', {
      agentId: agent.id,
      name: agent.name,
      projectId: agent.projectId,
    });

    return agent;
  }

  async listByProject(projectId: number): Promise<Agent[]> {
    return this.prisma.agent.findMany({
      where: { projectId },
      include: {
        capabilities: true,
      },
      orderBy: { name: 'asc' },
    });
  }

  async getById(id: string): Promise<Agent | null> {
    return this.prisma.agent.findUnique({
      where: { id },
      include: {
        capabilities: true,
      },
    });
  }

  async update(
    id: string,
    data: Partial<RegisterAgentInput>
  ): Promise<Agent> {
    return this.prisma.agent.update({
      where: { id },
      data: {
        description: data.description,
        entryPath: data.entryPath,
        version: data.version,
        riskLevel: data.riskLevel,
      },
      include: {
        capabilities: true,
      },
    });
  }

  async delete(id: string): Promise<void> {
    await this.prisma.agent.delete({
      where: { id },
    });

    logger.info('Agent deleted', { agentId: id });
  }
}
