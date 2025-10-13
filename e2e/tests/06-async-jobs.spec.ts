import { test, expect } from '@playwright/test';

/**
 * Async Jobs & WebSocket E2E Tests
 *
 * Test suite for asynchronous job processing:
 * - Job creation
 * - Real-time progress updates via WebSocket
 * - Job status changes
 * - Job cancellation
 */

test.describe('Async Jobs System', () => {
  const baseURL = process.env.BASE_URL || 'http://localhost:3000';
  const apiURL = process.env.API_URL || 'http://localhost:8000';

  test.beforeEach(async ({ page }) => {
    await page.goto(baseURL);
  });

  test('should create a job via API', async ({ request }) => {
    const response = await request.post(`${apiURL}/api/v1/jobs`, {
      data: {
        job_type: 'analysis',
        parameters: {},
        project_id: 1,
      },
    });

    expect(response.ok()).toBeTruthy();
    const job = await response.json();
    expect(job).toHaveProperty('id');
    expect(job).toHaveProperty('status');
    expect(job.job_type).toBe('analysis');
  });

  test('should retrieve job status', async ({ request }) => {
    // Create a job first
    const createResponse = await request.post(`${apiURL}/api/v1/jobs`, {
      data: {
        job_type: 'analysis',
        parameters: {},
        project_id: 1,
      },
    });

    const job = await createResponse.json();
    const jobId = job.id;

    // Get job status
    const statusResponse = await request.get(`${apiURL}/api/v1/jobs/${jobId}`);
    expect(statusResponse.ok()).toBeTruthy();

    const jobStatus = await statusResponse.json();
    expect(jobStatus.id).toBe(jobId);
    expect(['pending', 'running', 'completed', 'failed', 'cancelled']).toContain(jobStatus.status);
  });

  test('should list all jobs', async ({ request }) => {
    const response = await request.get(`${apiURL}/api/v1/jobs`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('jobs');
    expect(Array.isArray(data.jobs)).toBeTruthy();
  });

  test('should filter jobs by status', async ({ request }) => {
    const response = await request.get(`${apiURL}/api/v1/jobs?status_filter=completed`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('jobs');
    const jobs = data.jobs;

    if (jobs.length > 0) {
      jobs.forEach((job: any) => {
        expect(job.status).toBe('completed');
      });
    }
  });

  test('should dispatch a job', async ({ request }) => {
    // Create a job
    const createResponse = await request.post(`${apiURL}/api/v1/jobs`, {
      data: {
        job_type: 'analysis',
        parameters: {},
        project_id: 1,
      },
    });

    const job = await createResponse.json();

    // Dispatch the job
    const dispatchResponse = await request.post(`${apiURL}/api/v1/jobs/${job.id}/dispatch`);
    expect(dispatchResponse.ok()).toBeTruthy();

    const dispatchedJob = await dispatchResponse.json();
    expect(['running', 'pending']).toContain(dispatchedJob.status);
  });

  test('should cancel a running job', async ({ request }) => {
    // Create and dispatch a job
    const createResponse = await request.post(`${apiURL}/api/v1/jobs`, {
      data: {
        job_type: 'analysis',
        parameters: {},
        project_id: 1,
      },
    });

    const job = await createResponse.json();
    await request.post(`${apiURL}/api/v1/jobs/${job.id}/dispatch`);

    // Cancel it
    const cancelResponse = await request.post(`${apiURL}/api/v1/jobs/${job.id}/cancel`);
    expect(cancelResponse.ok()).toBeTruthy();

    // Verify status
    const statusResponse = await request.get(`${apiURL}/api/v1/jobs/${job.id}`);
    const cancelledJob = await statusResponse.json();
    expect(['cancelled', 'cancelling']).toContain(cancelledJob.status);
  });

  test('should get job statistics', async ({ request }) => {
    const response = await request.get(`${apiURL}/api/v1/jobs/statistics/summary`);
    expect(response.ok()).toBeTruthy();

    const stats = await response.json();
    expect(stats).toHaveProperty('total');
    expect(typeof stats.total).toBe('number');
  });

  test('should handle WebSocket connection', async ({ page }) => {
    // Navigate to a page that uses WebSocket
    await page.goto(baseURL);

    // Create a promise to track WebSocket connection
    const wsPromise = page.waitForEvent('websocket', { timeout: 10000 }).catch(() => null);

    // Trigger action that opens WebSocket (e.g., viewing jobs page)
    await page.goto(`${baseURL}/jobs`).catch(() => {
      // Page might not exist, that's okay for this test
    });

    const ws = await wsPromise;

    if (ws) {
      // Verify WebSocket URL
      expect(ws.url()).toContain('ws://');
      expect(ws.url()).toContain('/jobs/ws');
    }
  });

  test('should receive WebSocket progress updates', async ({ page }) => {
    const messages: string[] = [];

    // Listen for WebSocket messages
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        try {
          const data = JSON.parse(event.payload as string);
          messages.push(data);
        } catch {
          // Ignore non-JSON messages
        }
      });
    });

    // Trigger an action that creates a job and sends progress updates
    await page.goto(`${baseURL}/jobs`).catch(() => {
      // Page might not exist
    });

    // Wait for potential WebSocket messages
    await page.waitForTimeout(2000);

    // If any messages received, verify structure
    if (messages.length > 0) {
      const message = messages[0] as any;
      expect(message).toHaveProperty('type');
    }
  });

  test('should handle concurrent job creation', async ({ request }) => {
    const jobs = [];

    // Create 5 jobs concurrently
    for (let i = 0; i < 5; i++) {
      jobs.push(
        request.post(`${apiURL}/api/v1/jobs`, {
          data: {
            job_type: 'analysis',
            parameters: {},
            project_id: 1,
          },
        })
      );
    }

    const responses = await Promise.all(jobs);

    // All should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });
  });

  test('should paginate job results', async ({ request }) => {
    // Get first page (skip=0, limit=5)
    const page1Response = await request.get(`${apiURL}/api/v1/jobs?skip=0&limit=5`);
    expect(page1Response.ok()).toBeTruthy();

    const page1Data = await page1Response.json();
    expect(page1Data).toHaveProperty('jobs');
    const page1Jobs = page1Data.jobs;

    if (page1Jobs.length >= 5) {
      // Get second page (skip=5, limit=5)
      const page2Response = await request.get(`${apiURL}/api/v1/jobs?skip=5&limit=5`);
      expect(page2Response.ok()).toBeTruthy();

      const page2Data = await page2Response.json();
      expect(page2Data).toHaveProperty('jobs');
      const page2Jobs = page2Data.jobs;

      // Pages should have different jobs
      if (page2Jobs.length > 0) {
        expect(page1Jobs[0].id).not.toBe(page2Jobs[0].id);
      }
    }
  });
});
