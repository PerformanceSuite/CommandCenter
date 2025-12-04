import { connect, Client, Container } from '@dagger.io/dagger';
import logger from '../utils/logger';
import {
  AgentExecutionConfig,
  AgentExecutionResult,
} from './types';

export class DaggerAgentExecutor {
  async connect(): Promise<void> {
    // Dagger SDK connect() doesn't return a reusable client
    // Connection is managed per-operation via connect()
    logger.info('Dagger SDK ready');
  }

  async executeAgent(
    agentPath: string,
    input: unknown,
    config: AgentExecutionConfig
  ): Promise<AgentExecutionResult> {
    const startTime = Date.now();

    try {
      let result: string = '';

      // Connect to Dagger for this operation
      await connect(async (client) => {
        // 1. Create isolated container
        let container = client
          .container()
          .from('node:20-alpine')
          .withDirectory('/workspace', client.host().directory('.'))
          .withWorkdir('/workspace')
          .withExec(['npm', 'install']);

        // 2. Inject secrets (if needed)
        if (config.secrets) {
          for (const [key, value] of Object.entries(config.secrets)) {
            const secret = client.setSecret(key, value);
            container = container.withSecretVariable(key, secret);
          }
        }

        // 3. Apply resource limits
        container = container.withEnvVariable(
          'NODE_OPTIONS',
          `--max-old-space-size=${config.maxMemoryMb}`
        );

        // 4. Install tsx for TypeScript execution (if .ts file)
        const isTypeScript = agentPath.endsWith('.ts');
        if (isTypeScript) {
          container = container.withExec(['npm', 'install', '-g', 'tsx']);
        }

        // 5. Execute agent with timeout
        const runtime = isTypeScript ? 'tsx' : 'node';
        result = await container
          .withExec([
            'timeout',
            config.timeoutSeconds.toString(),
            runtime,
            agentPath,
            JSON.stringify(input),
          ])
          .stdout();
      });

      // 6. Parse and validate output
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
    // Dagger SDK manages connection lifecycle automatically
    logger.info('Dagger SDK cleanup complete');
  }
}

export const daggerExecutor = new DaggerAgentExecutor();
export default daggerExecutor;
