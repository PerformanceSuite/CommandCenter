import { connect, NatsConnection, StringCodec } from 'nats';
import logger from '../utils/logger';
import config from '../config';

export class NatsClient {
  private connection: NatsConnection | null = null;
  private codec = StringCodec();

  async connect(): Promise<void> {
    try {
      this.connection = await connect({
        servers: config.natsUrl,
      });
      logger.info('Connected to NATS', { url: config.natsUrl });
    } catch (error) {
      logger.error('Failed to connect to NATS', { error });
      throw error;
    }
  }

  async publish(subject: string, data: unknown): Promise<void> {
    if (!this.connection) {
      throw new Error('NATS not connected');
    }

    const payload = this.codec.encode(JSON.stringify(data));
    this.connection.publish(subject, payload);
    logger.debug('Published NATS message', { subject, data });
  }

  async subscribe(
    subject: string,
    handler: (data: unknown) => Promise<void>
  ): Promise<void> {
    if (!this.connection) {
      throw new Error('NATS not connected');
    }

    const sub = this.connection.subscribe(subject);
    logger.info('Subscribed to NATS subject', { subject });

    (async () => {
      for await (const msg of sub) {
        try {
          const data = JSON.parse(this.codec.decode(msg.data));
          await handler(data);
        } catch (error) {
          logger.error('Error handling NATS message', {
            subject,
            error,
          });
        }
      }
    })();
  }

  isConnected(): boolean {
    return this.connection !== null && !this.connection.isClosed();
  }

  async close(): Promise<void> {
    if (this.connection) {
      await this.connection.drain();
      logger.info('NATS connection closed');
    }
  }
}

export const natsClient = new NatsClient();
export default natsClient;
