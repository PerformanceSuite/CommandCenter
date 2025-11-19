import { describe, it, expect } from 'vitest';
import { createServer } from './server';
import request from 'supertest';

describe('Express Server', () => {
  it('should respond to health check', async () => {
    const app = createServer();
    const response = await request(app).get('/api/health');

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('ok');
  });
});
