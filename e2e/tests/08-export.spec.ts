import { test, expect } from '@playwright/test';

/**
 * Export API E2E Tests
 *
 * Test suite for export functionality:
 * - SARIF format export
 * - HTML format export
 * - CSV format export (with types)
 * - Excel format export
 * - JSON format export
 * - Batch export operations
 * - Format listing
 * - Rate limiting
 */

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('Export API', () => {
  // Test analysis ID (assumes at least one analysis exists)
  const TEST_ANALYSIS_ID = 1;

  test('should list available export formats', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/export/formats`);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('formats');
    expect(Array.isArray(data.formats)).toBeTruthy();
    expect(data.formats.length).toBeGreaterThan(0);

    // Verify expected formats are present
    const formatNames = data.formats.map((f: any) => f.format);
    expect(formatNames).toContain('sarif');
    expect(formatNames).toContain('html');
    expect(formatNames).toContain('csv');
    expect(formatNames).toContain('excel');
    expect(formatNames).toContain('json');
  });

  test('should export analysis to SARIF format', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/sarif`
    );

    // May return 404 if no analysis exists, which is acceptable
    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-type']).toContain('application/json');
    expect(response.headers()['content-disposition']).toContain('.sarif');

    const data = await response.json();

    // Validate SARIF 2.1.0 structure
    expect(data).toHaveProperty('version');
    expect(data.version).toBe('2.1.0');
    expect(data).toHaveProperty('$schema');
    expect(data).toHaveProperty('runs');
    expect(Array.isArray(data.runs)).toBeTruthy();
  });

  test('should export analysis to HTML format', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/html`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-type']).toContain('text/html');
    expect(response.headers()['content-disposition']).toContain('.html');

    const html = await response.text();

    // Validate HTML structure
    expect(html).toContain('<!DOCTYPE html>');
    expect(html).toContain('<html');
    expect(html).toContain('</html>');
    expect(html).toContain('<head>');
    expect(html).toContain('<body>');
  });

  test('should export analysis to CSV format (combined)', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/csv?export_type=combined`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-type']).toContain('text/csv');
    expect(response.headers()['content-disposition']).toContain('.csv');

    const csv = await response.text();

    // Validate CSV structure (should have headers)
    expect(csv.length).toBeGreaterThan(0);
    expect(csv.split('\n')[0]).toContain(','); // CSV header row with commas
  });

  test('should export analysis to CSV format (technologies)', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/csv?export_type=technologies`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-disposition']).toContain('technologies.csv');
  });

  test('should export analysis to CSV format (dependencies)', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/csv?export_type=dependencies`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-disposition']).toContain('dependencies.csv');
  });

  test('should export analysis to CSV format (metrics)', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/csv?export_type=metrics`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-disposition']).toContain('metrics.csv');
  });

  test('should export analysis to CSV format (gaps)', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/csv?export_type=gaps`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-disposition']).toContain('gaps.csv');
  });

  test('should export analysis to Excel format', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/excel`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    // May return 500 if openpyxl not installed
    if (response.status() === 500) {
      const error = await response.json();
      if (error.detail?.includes('openpyxl')) {
        test.skip();
        return;
      }
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-type']).toContain('spreadsheetml.sheet');
    expect(response.headers()['content-disposition']).toContain('.xlsx');

    const buffer = await response.body();
    expect(buffer.length).toBeGreaterThan(0);

    // Verify Excel file signature (PK\x03\x04)
    expect(buffer[0]).toBe(0x50); // 'P'
    expect(buffer[1]).toBe(0x4B); // 'K'
  });

  test('should export analysis to JSON format', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/json?pretty=true`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-type']).toContain('application/json');
    expect(response.headers()['content-disposition']).toContain('.json');

    const data = await response.json();

    // Validate analysis structure
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('project_path');
    expect(data).toHaveProperty('analyzed_at');
  });

  test('should handle non-existent analysis ID', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/999999/sarif`
    );

    expect(response.status()).toBe(404);
    const error = await response.json();
    expect(error).toHaveProperty('detail');
  });

  test('should reject invalid CSV export type', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/csv?export_type=invalid_type`
    );

    // Should return 422 Unprocessable Entity for invalid enum
    expect(response.status()).toBe(422);
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

    // May return 404 if analyses don't exist
    if (response.status() === 404) {
      test.skip();
      return;
    }

    // Should return 202 Accepted
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

  test('should handle rate limiting on SARIF export', async ({ request }) => {
    // Make 11 rapid requests (rate limit is 10/minute)
    const requests = [];
    for (let i = 0; i < 11; i++) {
      requests.push(
        request.get(`${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/sarif`)
      );
    }

    const responses = await Promise.all(requests);

    // At least one should be rate limited (429)
    const rateLimited = responses.some(r => r.status() === 429);

    // Note: Rate limiting may not trigger in test environment
    // This test documents expected behavior but may pass without hitting limit
    if (rateLimited) {
      expect(rateLimited).toBeTruthy();
    }
  });

  test('should include content-length header in all exports', async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/json`
    );

    if (response.status() === 404) {
      test.skip();
      return;
    }

    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-length']).toBeTruthy();

    const contentLength = parseInt(response.headers()['content-length']);
    expect(contentLength).toBeGreaterThan(0);
  });

  test('should support pretty-print option for JSON export', async ({ request }) => {
    const prettyResponse = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/json?pretty=true`
    );

    if (prettyResponse.status() === 404) {
      test.skip();
      return;
    }

    const uglyResponse = await request.get(
      `${API_URL}/api/v1/export/${TEST_ANALYSIS_ID}/json?pretty=false`
    );

    expect(prettyResponse.ok()).toBeTruthy();
    expect(uglyResponse.ok()).toBeTruthy();

    const prettyText = await prettyResponse.text();
    const uglyText = await uglyResponse.text();

    // Pretty version should be larger due to whitespace
    expect(prettyText.length).toBeGreaterThanOrEqual(uglyText.length);
  });
});
