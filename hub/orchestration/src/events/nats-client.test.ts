import { describe, it, expect } from 'vitest';
import { NatsClient } from './nats-client';

describe('NatsClient', () => {
  it('should create NatsClient instance', () => {
    const client = new NatsClient();
    expect(client).toBeDefined();
    expect(client.connect).toBeDefined();
    expect(client.publish).toBeDefined();
    expect(client.subscribe).toBeDefined();
  });

  it('should throw if publishing before connect', async () => {
    const client = new NatsClient();
    await expect(client.publish('test', {})).rejects.toThrow('not connected');
  });
});
