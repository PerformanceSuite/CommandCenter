import { connect, Client, Container } from '@dagger.io/dagger';
import logger from '../utils/logger';
import {
  AgentExecutionConfig,
  AgentExecutionResult,
} from './types';

export class DaggerAgentExecutor {
  private client: Client | null = null;

  async connect(): Promise<void> {
    this.client = await connect();
    logger.info('Connected to Dagger engine');
  }

  async executeAgent(
    agentPath: string,
    input: unknown,
    config: AgentExecutionConfig
  ): Promise<AgentExecutionResult> {
    if (!this.client) {
      throw new Error('Dagger client not connected');
    }

    const startTime = Date.now();

    try {
      // 1. Create isolated container
      let container = this.client
        .container()
        .from('node:20-alpine')
        .withDirectory('/workspace', this.client.host().directory('.'))
        .withWorkdir('/workspace')
        .withExec(['npm', 'install']);

      // 2. Inject secrets (if needed)
      if (config.secrets) {
        for (const [key, value] of Object.entries(config.secrets)) {
          const secret = this.client.setSecret(key, value);
          container = container.withSecretVariable(key, secret);
        }
      }

      // 3. Apply resource limits
      container = container.withEnvVariable(
        'NODE_OPTIONS',
        `--max-old-space-size=${config.maxMemoryMb}`
      );

      // 4. Execute agent with timeout
      const result = await container
        .withExec([
          'timeout',
          config.timeoutSeconds.toString(),
          'node',
          agentPath,
          JSON.stringify(input),
        ])
        .stdout();

      // 5. Parse and validate output
      const output = JSON.parse(result);
      // TODO: Validate against outputSchema using Zod

      return {
        success: true,
        output,
        executionTimeMs: Date.now() - startTime,
      };
    } catch (error: any) {
      logger.error('Agent execution failed', { agentPath, error });
      return {
        success: false,
        error: error.message,
        executionTimeMs: Date.now() - startTime,
      };
    }
  }

  async close(): Promise<void> {
    if (this.client) {
      await this.client.close();
      logger.info('Dagger connection closed');
    }
  }
}

export const daggerExecutor = new DaggerAgentExecutor();
export default daggerExecutor;
