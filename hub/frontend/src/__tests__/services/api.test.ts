/**
 * Tests for Hub API client
 *
 * Tests all API client methods with mocked fetch.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { projectsApi, orchestrationApi, filesystemApi } from '../../services/api';
import { mockProjects, mockStats, mockOperationResponse, createMockResponse } from '../../test-utils/mocks';

describe('Projects API', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('list() fetches all projects', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(mockProjects)
    );

    const result = await projectsApi.list();

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/projects/',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
    expect(result).toEqual(mockProjects);
  });

  it('get() fetches a single project', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(mockProjects[0])
    );

    const result = await projectsApi.get(1);

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/projects/1',
      expect.any(Object)
    );
    expect(result).toEqual(mockProjects[0]);
  });

  it('create() creates a new project', async () => {
    const newProject = mockProjects[0];
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(newProject)
    );

    const result = await projectsApi.create({
      name: 'NewProject',
      path: '/tmp/new-project',
    });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/projects/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          name: 'NewProject',
          path: '/tmp/new-project',
        }),
      })
    );
    expect(result).toEqual(newProject);
  });

  it('delete() deletes a project', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(null)
    );

    await projectsApi.delete(1, false);

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/projects/1?delete_files=false',
      expect.objectContaining({
        method: 'DELETE',
      })
    );
  });

  it('delete() with deleteFiles=true includes parameter', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(null)
    );

    await projectsApi.delete(1, true);

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/projects/1?delete_files=true',
      expect.any(Object)
    );
  });

  it('stats() fetches project statistics', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(mockStats)
    );

    const result = await projectsApi.stats();

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/projects/stats',
      expect.any(Object)
    );
    expect(result).toEqual(mockStats);
  });

  it('handles API errors correctly', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse({ detail: 'Project not found' }, false)
    );

    await expect(projectsApi.get(999)).rejects.toThrow('Project not found');
  });
});

describe('Orchestration API', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('start() starts a project', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(mockOperationResponse)
    );

    const result = await orchestrationApi.start(1);

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/orchestration/1/start',
      expect.objectContaining({
        method: 'POST',
      })
    );
    expect(result).toEqual(mockOperationResponse);
  });

  it('stop() stops a project', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse({ ...mockOperationResponse, status: 'stopped' })
    );

    const result = await orchestrationApi.stop(1);

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/orchestration/1/stop',
      expect.objectContaining({
        method: 'POST',
      })
    );
    expect(result.status).toBe('stopped');
  });

  it('restart() restarts a project', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(mockOperationResponse)
    );

    const result = await orchestrationApi.restart(1);

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/orchestration/1/restart',
      expect.objectContaining({
        method: 'POST',
      })
    );
    expect(result).toEqual(mockOperationResponse);
  });

  it('status() gets project status', async () => {
    const statusResponse = {
      status: 'running',
      health: 'healthy',
      containers: [],
    };

    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(statusResponse)
    );

    const result = await orchestrationApi.status(1);

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/orchestration/1/status',
      expect.any(Object)
    );
    expect(result).toEqual(statusResponse);
  });

  it('health() gets project health', async () => {
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse({ ...mockOperationResponse, health: 'healthy' })
    );

    const result = await orchestrationApi.health(1);

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/orchestration/1/health',
      expect.any(Object)
    );
    expect(result).toBeDefined();
  });
});

describe('Filesystem API', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('getHome() fetches home directory', async () => {
    const homeResponse = { path: '/home/user' };
    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(homeResponse)
    );

    const result = await filesystemApi.getHome();

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/filesystem/home',
      expect.any(Object)
    );
    expect(result).toEqual(homeResponse);
  });

  it('browse() browses directory with path parameter', async () => {
    const browseResponse = {
      currentPath: '/tmp',
      parent: '/',
      directories: [
        { name: 'test-project', path: '/tmp/test-project' },
      ],
    };

    (global.fetch as any).mockResolvedValueOnce(
      createMockResponse(browseResponse)
    );

    const result = await filesystemApi.browse('/tmp');

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/filesystem/browse?path=%2Ftmp',
      expect.any(Object)
    );
    expect(result).toEqual(browseResponse);
  });
});
