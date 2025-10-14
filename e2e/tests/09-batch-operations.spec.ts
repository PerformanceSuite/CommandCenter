import { test, expect } from '@playwright/test';

/**
 * Batch Operations E2E Tests
 *
 * Test suite for batch operations functionality:
 * - Batch analysis of multiple repositories
 * - Batch export of multiple analyses
 * - Batch import of technologies
 * - Batch job tracking and status
 * - Batch statistics
 * - Error handling and validation
 */

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('Batch Operations API', () => {
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

    // May return 404 if repositories don't exist, or 400 if invalid
    if (response.status() === 404 || response.status() === 400) {
      test.skip();
      return;
    }

    expect(response.status()).toBe(202); // Accepted
    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('job_id');
    expect(data).toHaveProperty('job_type');
    expect(data.job_type).toBe('batch_analysis');
    expect(data).toHaveProperty('total_items');
    expect(data.total_items).toBe(2);
    expect(data).toHaveProperty('status');
    expect(data).toHaveProperty('repository_ids');
    expect(data.repository_ids).toEqual([1, 2]);
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

    expect(response.status()).toBe(202); // Accepted
    const data = await response.json();

    expect(data).toHaveProperty('job_id');
    expect(data).toHaveProperty('job_type');
    expect(data.job_type).toBe('batch_export');
    expect(data).toHaveProperty('total_items');
    expect(data.total_items).toBe(3);
    expect(data).toHaveProperty('format');
    expect(data.format).toBe('json');
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

  test('should reject batch export with invalid format', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/batch/export`, {
      data: {
        analysis_ids: [1],
        format: 'invalid_format',
      },
    });

    // Should return 422 Unprocessable Entity for invalid enum
    expect(response.status()).toBe(422);
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

    expect(response.status()).toBe(202); // Accepted
    const data = await response.json();

    expect(data).toHaveProperty('job_id');
    expect(data).toHaveProperty('job_type');
    expect(data.job_type).toBe('batch_import');
    expect(data).toHaveProperty('total_items');
    expect(data.total_items).toBe(2);
    expect(data).toHaveProperty('imported_count');
    expect(data).toHaveProperty('skipped_count');
    expect(data).toHaveProperty('failed_count');
  });

  test('should support all merge strategies', async ({ request }) => {
    const strategies = ['skip', 'overwrite', 'merge'];

    for (const strategy of strategies) {
      const response = await request.post(`${API_URL}/api/v1/batch/import`, {
        data: {
          technologies: [
            {
              title: `Test Tech ${strategy}`,
              domain: 'frontend',
            },
          ],
          project_id: 1,
          merge_strategy: strategy,
        },
      });

      if (response.status() === 404 || response.status() === 400) {
        continue;
      }

      expect(response.status()).toBe(202);
    }
  });

  test('should reject batch import with invalid merge strategy', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/batch/import`, {
      data: {
        technologies: [
          {
            title: 'Test',
            domain: 'frontend',
          },
        ],
        project_id: 1,
        merge_strategy: 'invalid_strategy',
      },
    });

    expect(response.status()).toBe(422);
  });

  test('should reject batch import with missing required fields', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/batch/import`, {
      data: {
        technologies: [
          {
            // Missing title
            domain: 'frontend',
          },
        ],
        project_id: 1,
      },
    });

    expect(response.status()).toBe(422);
  });

  test('should get batch statistics', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/batch/statistics`);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Validate statistics structure
    expect(data).toHaveProperty('total_batches');
    expect(data).toHaveProperty('active_batches');
    expect(data).toHaveProperty('by_type');
    expect(data).toHaveProperty('by_status');
    expect(data).toHaveProperty('average_duration_seconds');
    expect(data).toHaveProperty('success_rate');

    // Validate types
    expect(typeof data.total_batches).toBe('number');
    expect(typeof data.active_batches).toBe('number');
    expect(typeof data.success_rate).toBe('number');
  });

  test('should filter batch statistics by project', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/batch/statistics?project_id=1`
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('total_batches');
  });

  test('should get batch job details', async ({ request }) => {
    // First create a batch job
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

    // Now get job details
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

    // Poll for progress updates
    let attempts = 0;
    let completed = false;

    while (attempts < 10 && !completed) {
      await new Promise(resolve => setTimeout(resolve, 500));

      const statusResponse = await request.get(
        `${API_URL}/api/v1/batch/jobs/${jobId}`
      );

      if (!statusResponse.ok()) break;

      const statusData = await statusResponse.json();

      // Check for progress updates
      expect(statusData).toHaveProperty('progress');
      expect(statusData.progress).toBeGreaterThanOrEqual(0);
      expect(statusData.progress).toBeLessThanOrEqual(100);

      completed = statusData.status === 'completed' || statusData.status === 'failed';
      attempts++;
    }
  });

  test('should support batch analysis with custom parameters', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/batch/analyze`, {
      data: {
        repository_ids: [1],
        priority: 8,
        parameters: {
          analyze_dependencies: true,
          check_security: true,
          deep_scan: false,
          timeout_seconds: 300,
        },
        notify_on_complete: true,
        tags: ['priority', 'security-scan'],
      },
    });

    if (response.status() === 404 || response.status() === 400) {
      test.skip();
      return;
    }

    expect(response.status()).toBe(202);
    const data = await response.json();

    expect(data).toHaveProperty('job_id');
  });

  test('should handle concurrent batch operations', async ({ request }) => {
    const requests = [];

    // Create 5 concurrent batch operations
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

    // At least some should succeed
    const successful = responses.filter(r => r.status() === 202);
    expect(successful.length).toBeGreaterThan(0);

    // All successful responses should have unique job IDs
    const jobIds = await Promise.all(
      successful.map(r => r.json().then(data => data.job_id))
    );
    const uniqueJobIds = new Set(jobIds);
    expect(uniqueJobIds.size).toBe(jobIds.length);
  });

  test('should validate repository_ids array length', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/batch/analyze`, {
      data: {
        repository_ids: [], // Empty array
      },
    });

    expect(response.status()).toBe(400);
  });

  test('should validate analysis_ids array length', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/batch/export`, {
      data: {
        analysis_ids: [], // Empty array
        format: 'json',
      },
    });

    expect(response.status()).toBe(400);
  });

  test('should validate technologies array length', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/batch/import`, {
      data: {
        technologies: [], // Empty array
        project_id: 1,
      },
    });

    expect(response.status()).toBe(400);
  });
});
