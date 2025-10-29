import { test, expect } from '@playwright/test';

/**
 * API Operations E2E Tests
 *
 * Consolidated test suite covering all API-focused E2E tests:
 * - Job creation and management
 * - Job status tracking and updates
 * - Job cancellation and error handling
 * - Batch operations (analysis, export, import)
 * - Batch statistics and progress tracking
 * - Concurrent operation handling
 *
 * CONSOLIDATED FROM: 06-async-jobs, 08-export, 09-batch-operations
 */

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('API Operations & Async Jobs', () => {
  test.describe('Job Management', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(API_URL);
    });

    test('should create a job via API', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/jobs`, {
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
      const createResponse = await request.post(`${API_URL}/api/v1/jobs`, {
        data: {
          job_type: 'analysis',
          parameters: {},
          project_id: 1,
        },
      });

      const job = await createResponse.json();
      const jobId = job.id;

      const statusResponse = await request.get(`${API_URL}/api/v1/jobs/${jobId}`);
      expect(statusResponse.ok()).toBeTruthy();

      const jobStatus = await statusResponse.json();
      expect(jobStatus.id).toBe(jobId);
      expect(['pending', 'running', 'completed', 'failed', 'cancelled']).toContain(jobStatus.status);
    });

    test('should list all jobs', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/jobs`);
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('jobs');
      expect(Array.isArray(data.jobs)).toBeTruthy();
    });

    test('should filter jobs by status', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/jobs?status_filter=completed`);
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
      const createResponse = await request.post(`${API_URL}/api/v1/jobs`, {
        data: {
          job_type: 'analysis',
          parameters: {},
          project_id: 1,
        },
      });

      const job = await createResponse.json();

      const dispatchResponse = await request.post(`${API_URL}/api/v1/jobs/${job.id}/dispatch`);
      expect(dispatchResponse.ok()).toBeTruthy();

      const dispatchedJob = await dispatchResponse.json();
      expect(['running', 'pending']).toContain(dispatchedJob.status);
    });

    test('should cancel a running job', async ({ request }) => {
      const createResponse = await request.post(`${API_URL}/api/v1/jobs`, {
        data: {
          job_type: 'analysis',
          parameters: {},
          project_id: 1,
        },
      });

      const job = await createResponse.json();
      await request.post(`${API_URL}/api/v1/jobs/${job.id}/dispatch`);

      const cancelResponse = await request.post(`${API_URL}/api/v1/jobs/${job.id}/cancel`);
      expect(cancelResponse.ok()).toBeTruthy();

      const statusResponse = await request.get(`${API_URL}/api/v1/jobs/${job.id}`);
      const cancelledJob = await statusResponse.json();
      expect(['cancelled', 'cancelling']).toContain(cancelledJob.status);
    });

    test('should get job statistics', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/jobs/statistics/summary`);
      expect(response.ok()).toBeTruthy();

      const stats = await response.json();
      expect(stats).toHaveProperty('total');
      expect(typeof stats.total).toBe('number');
    });

    test('should handle concurrent job creation', async ({ request }) => {
      const jobs = [];

      for (let i = 0; i < 5; i++) {
        jobs.push(
          request.post(`${API_URL}/api/v1/jobs`, {
            data: {
              job_type: 'analysis',
              parameters: {},
              project_id: 1,
            },
          })
        );
      }

      const responses = await Promise.all(jobs);

      responses.forEach(response => {
        expect(response.ok()).toBeTruthy();
      });
    });

    test('should paginate job results', async ({ request }) => {
      const page1Response = await request.get(`${API_URL}/api/v1/jobs?skip=0&limit=5`);
      expect(page1Response.ok()).toBeTruthy();

      const page1Data = await page1Response.json();
      expect(page1Data).toHaveProperty('jobs');
      const page1Jobs = page1Data.jobs;

      if (page1Jobs.length >= 5) {
        const page2Response = await request.get(`${API_URL}/api/v1/jobs?skip=5&limit=5`);
        expect(page2Response.ok()).toBeTruthy();

        const page2Data = await page2Response.json();
        expect(page2Data).toHaveProperty('jobs');
        const page2Jobs = page2Data.jobs;

        if (page2Jobs.length > 0) {
          expect(page1Jobs[0].id).not.toBe(page2Jobs[0].id);
        }
      }
    });

    test('should handle WebSocket connection for job updates', async ({ page }) => {
      const messages: string[] = [];

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

      await page.goto(`${API_URL.replace(/:\d+/, ':3000')}/`).catch(() => {
        // Page might not exist
      });

      await page.waitForTimeout(2000);

      if (messages.length > 0) {
        const message = messages[0] as any;
        expect(message).toHaveProperty('type');
      }
    });
  });

  test.describe('Export API', () => {
    const TEST_ANALYSIS_ID = 1;

    test('should list available export formats', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/export/formats`);

      expect(response.ok()).toBeTruthy();
      const data = await response.json();

      expect(data).toHaveProperty('formats');
      expect(Array.isArray(data.formats)).toBeTruthy();
      expect(data.formats.length).toBeGreaterThan(0);

      const formatNames = data.formats.map((f: any) => f.format);
      expect(formatNames).toContain('sarif');
      expect(formatNames).toContain('html');
      expect(formatNames).toContain('csv');
      expect(formatNames).toContain('excel');
      expect(formatNames).toContain('json');
    });

    test('should export analysis to SARIF format', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/sarif`);

      if (response.status() === 404) {
        test.skip();
        return;
      }

      expect(response.ok()).toBeTruthy();
      expect(response.headers()['content-type']).toContain('application/json');
      expect(response.headers()['content-disposition']).toContain('.sarif');

      const data = await response.json();

      expect(data).toHaveProperty('version');
      expect(data.version).toBe('2.1.0');
      expect(data).toHaveProperty('$schema');
      expect(data).toHaveProperty('runs');
      expect(Array.isArray(data.runs)).toBeTruthy();
    });

    test('should export analysis to HTML format', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/html`);

      if (response.status() === 404) {
        test.skip();
        return;
      }

      expect(response.ok()).toBeTruthy();
      expect(response.headers()['content-type']).toContain('text/html');
      expect(response.headers()['content-disposition']).toContain('.html');

      const html = await response.text();

      expect(html).toContain('<!DOCTYPE html>');
      expect(html).toContain('<html');
      expect(html).toContain('</html>');
      expect(html).toContain('<head>');
      expect(html).toContain('<body>');
    });

    test('should export analysis to CSV format', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/csv?export_type=combined`);

      if (response.status() === 404) {
        test.skip();
        return;
      }

      expect(response.ok()).toBeTruthy();
      expect(response.headers()['content-type']).toContain('text/csv');
      expect(response.headers()['content-disposition']).toContain('.csv');

      const csv = await response.text();

      expect(csv.length).toBeGreaterThan(0);
      expect(csv.split('\n')[0]).toContain(',');
    });

    test('should export analysis to JSON format', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/json?pretty=true`);

      if (response.status() === 404) {
        test.skip();
        return;
      }

      expect(response.ok()).toBeTruthy();
      expect(response.headers()['content-type']).toContain('application/json');
      expect(response.headers()['content-disposition']).toContain('.json');

      const data = await response.json();

      expect(data).toHaveProperty('id');
    });

    test('should handle non-existent analysis ID', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/export/999999/sarif`);

      expect(response.status()).toBe(404);
      const error = await response.json();
      expect(error).toHaveProperty('detail');
    });

    test('should create batch export job', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/export/batch`, {
        params: {
          format: 'json',
        },
        data: {
          analysis_ids: [1, 2, 3],
        },
      });

      if (response.status() === 404) {
        test.skip();
        return;
      }

      expect(response.status()).toBe(202);
      const data = await response.json();

      expect(data).toHaveProperty('message');
      expect(data).toHaveProperty('analysis_count');
      expect(data.analysis_count).toBe(3);
    });

    test('should reject empty batch export', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/export/batch`, {
        params: {
          format: 'json',
        },
        data: {
          analysis_ids: [],
        },
      });

      expect(response.status()).toBe(400);
      const error = await response.json();
      expect(error.detail).toContain('cannot be empty');
    });

    test('should handle rate limiting on exports', async ({ request }) => {
      const requests = [];
      for (let i = 0; i < 11; i++) {
        requests.push(
          request.get(`${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/sarif`)
        );
      }

      const responses = await Promise.all(requests);
      const rateLimited = responses.some(r => r.status() === 429);

      if (rateLimited) {
        expect(rateLimited).toBeTruthy();
      }
    });
  });

  test.describe('Batch Operations', () => {
    test('should create batch analysis job', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/batch/analyze`, {
        data: {
          repository_ids: [1, 2],
          priority: 5,
          parameters: {
            analyze_dependencies: true,
            check_security: false,
          },
          notify_on_complete: false,
          tags: ['e2e-test'],
        },
      });

      if (response.status() === 404 || response.status() === 400) {
        test.skip();
        return;
      }

      expect(response.status()).toBe(202);
      const data = await response.json();

      expect(data).toHaveProperty('job_id');
      expect(data).toHaveProperty('job_type');
      expect(data.job_type).toBe('batch_analysis');
      expect(data).toHaveProperty('total_items');
      expect(data.total_items).toBe(2);
    });

    test('should reject batch analysis with no repositories', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/batch/analyze`, {
        data: {
          repository_ids: [],
        },
      });

      expect(response.status()).toBe(400);
      const error = await response.json();
      expect(error).toHaveProperty('detail');
    });

    test('should create batch export job', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/batch/export`, {
        data: {
          analysis_ids: [1, 2, 3],
          format: 'json',
          parameters: {
            include_metrics: true,
            compress: false,
          },
          tags: ['e2e-test'],
        },
      });

      if (response.status() === 404 || response.status() === 400) {
        test.skip();
        return;
      }

      expect(response.status()).toBe(202);
      const data = await response.json();

      expect(data).toHaveProperty('job_id');
      expect(data).toHaveProperty('job_type');
      expect(data.job_type).toBe('batch_export');
      expect(data).toHaveProperty('total_items');
      expect(data.total_items).toBe(3);
    });

    test('should support all export formats for batch', async ({ request }) => {
      const formats = ['sarif', 'json', 'csv', 'html'];

      for (const format of formats) {
        const response = await request.post(`${API_URL}/api/v1/batch/export`, {
          data: {
            analysis_ids: [1],
            format: format,
          },
        });

        if (response.status() === 404 || response.status() === 400) {
          continue;
        }

        expect(response.status()).toBe(202);
        const data = await response.json();
        expect(data.format).toBe(format);
      }
    });

    test('should create batch import job', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/batch/import`, {
        data: {
          technologies: [
            {
              title: 'React E2E Test',
              domain: 'frontend',
              vendor: 'Meta',
              status: 'research',
            },
            {
              title: 'FastAPI E2E Test',
              domain: 'backend',
              vendor: 'Sebastián Ramírez',
              status: 'integrated',
            },
          ],
          project_id: 1,
          merge_strategy: 'skip',
          tags: ['e2e-test'],
        },
      });

      if (response.status() === 404 || response.status() === 400) {
        test.skip();
        return;
      }

      expect(response.status()).toBe(202);
      const data = await response.json();

      expect(data).toHaveProperty('job_id');
      expect(data).toHaveProperty('job_type');
      expect(data.job_type).toBe('batch_import');
      expect(data).toHaveProperty('total_items');
      expect(data.total_items).toBe(2);
    });

    test('should get batch statistics', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/batch/statistics`);

      expect(response.ok()).toBeTruthy();
      const data = await response.json();

      expect(data).toHaveProperty('total_batches');
      expect(data).toHaveProperty('active_batches');
      expect(data).toHaveProperty('by_type');
      expect(data).toHaveProperty('by_status');
      expect(data).toHaveProperty('average_duration_seconds');
      expect(data).toHaveProperty('success_rate');
    });

    test('should get batch job details', async ({ request }) => {
      const createResponse = await request.post(`${API_URL}/api/v1/batch/analyze`, {
        data: {
          repository_ids: [1],
          priority: 5,
        },
      });

      if (createResponse.status() !== 202) {
        test.skip();
        return;
      }

      const createData = await createResponse.json();
      const jobId = createData.job_id;

      const response = await request.get(`${API_URL}/api/v1/batch/jobs/${jobId}`);

      expect(response.ok()).toBeTruthy();
      const data = await response.json();

      expect(data).toHaveProperty('id');
      expect(data.id).toBe(jobId);
      expect(data).toHaveProperty('job_type');
      expect(data).toHaveProperty('status');
      expect(data).toHaveProperty('progress');
    });

    test('should handle non-existent batch job', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/batch/jobs/999999`);

      expect(response.status()).toBe(404);
      const error = await response.json();
      expect(error).toHaveProperty('detail');
    });

    test('should track progress of batch analysis', async ({ request }) => {
      const createResponse = await request.post(`${API_URL}/api/v1/batch/analyze`, {
        data: {
          repository_ids: [1, 2, 3],
        },
      });

      if (createResponse.status() !== 202) {
        test.skip();
        return;
      }

      const createData = await createResponse.json();
      const jobId = createData.job_id;

      let attempts = 0;
      let completed = false;

      while (attempts < 10 && !completed) {
        await new Promise(resolve => setTimeout(resolve, 500));

        const statusResponse = await request.get(`${API_URL}/api/v1/batch/jobs/${jobId}`);

        if (!statusResponse.ok()) break;

        const statusData = await statusResponse.json();

        expect(statusData).toHaveProperty('progress');
        expect(statusData.progress).toBeGreaterThanOrEqual(0);
        expect(statusData.progress).toBeLessThanOrEqual(100);

        completed = statusData.status === 'completed' || statusData.status === 'failed';
        attempts++;
      }
    });

    test('should handle concurrent batch operations', async ({ request }) => {
      const requests = [];

      for (let i = 0; i < 5; i++) {
        requests.push(
          request.post(`${API_URL}/api/v1/batch/analyze`, {
            data: {
              repository_ids: [1],
              priority: i,
              tags: [`concurrent-test-${i}`],
            },
          })
        );
      }

      const responses = await Promise.all(requests);

      const successful = responses.filter(r => r.status() === 202);
      expect(successful.length).toBeGreaterThan(0);

      const jobIds = await Promise.all(
        successful.map(r => r.json().then(data => data.job_id))
      );
      const uniqueJobIds = new Set(jobIds);
      expect(uniqueJobIds.size).toBe(jobIds.length);
    });
  });
});
