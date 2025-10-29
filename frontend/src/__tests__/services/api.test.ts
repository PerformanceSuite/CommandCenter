import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { api } from '../../services/api';
import { mockRepository, mockTechnology } from '../../tests/utils';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios, true);

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock axios.create to return a mock instance
    const mockInstance = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    };

    mockedAxios.create = vi.fn(() => mockInstance as any);
  });

  describe('Repository operations', () => {
    it('fetches all repositories', async () => {
      const repos = [mockRepository(), mockRepository({ id: 2 })];
      const mockGet = vi.fn().mockResolvedValue({ data: repos });

      // Replace the client's get method
      (api as any).client.get = mockGet;

      const result = await api.getRepositories();

      expect(mockGet).toHaveBeenCalledWith('/api/v1/repositories');
      expect(result).toEqual(repos);
    });

    it('fetches single repository', async () => {
      const repo = mockRepository();
      const mockGet = vi.fn().mockResolvedValue({ data: repo });
      (api as any).client.get = mockGet;

      const result = await api.getRepository('1');

      expect(mockGet).toHaveBeenCalledWith('/api/v1/repositories/1');
      expect(result).toEqual(repo);
    });

    it('creates repository', async () => {
      const newRepo = mockRepository();
      const mockPost = vi.fn().mockResolvedValue({ data: newRepo });
      (api as any).client.post = mockPost;

      const repoData = { owner: 'test', name: 'repo' };
      const result = await api.createRepository(repoData);

      expect(mockPost).toHaveBeenCalledWith('/api/v1/repositories', repoData);
      expect(result).toEqual(newRepo);
    });

    it('updates repository', async () => {
      const updated = mockRepository({ description: 'Updated' });
      const mockPut = vi.fn().mockResolvedValue({ data: updated });
      (api as any).client.put = mockPut;

      const updateData = { description: 'Updated' };
      const result = await api.updateRepository('1', updateData);

      expect(mockPut).toHaveBeenCalledWith('/api/v1/repositories/1', updateData);
      expect(result).toEqual(updated);
    });

    it('deletes repository', async () => {
      const mockDelete = vi.fn().mockResolvedValue({});
      (api as any).client.delete = mockDelete;

      await api.deleteRepository('1');

      expect(mockDelete).toHaveBeenCalledWith('/api/v1/repositories/1');
    });

    it('syncs repository', async () => {
      const mockPost = vi.fn().mockResolvedValue({});
      (api as any).client.post = mockPost;

      await api.syncRepository('1');

      expect(mockPost).toHaveBeenCalledWith('/api/v1/repositories/1/sync');
    });
  });

  describe('Technology operations', () => {
    it('fetches all technologies', async () => {
      const techs = [mockTechnology(), mockTechnology({ id: 2 })];
      const mockGet = vi.fn().mockResolvedValue({ data: techs });
      (api as any).client.get = mockGet;

      const result = await api.getTechnologies();

      expect(mockGet).toHaveBeenCalledWith('/api/v1/technologies');
      expect(result).toEqual(techs);
    });

    it('creates technology', async () => {
      const newTech = mockTechnology();
      const mockPost = vi.fn().mockResolvedValue({ data: newTech });
      (api as any).client.post = mockPost;

      const techData = { title: 'Python', domain: 'ai-ml' };
      const result = await api.createTechnology(techData);

      expect(mockPost).toHaveBeenCalledWith('/api/v1/technologies', techData);
      expect(result).toEqual(newTech);
    });
  });

  describe('Knowledge Base operations', () => {
    it('queries knowledge base', async () => {
      const mockResponse = { answer: 'Test answer', sources: [] };
      const mockPost = vi.fn().mockResolvedValue({ data: mockResponse });
      (api as any).client.post = mockPost;

      const result = await api.queryKnowledge('test query');

      expect(mockPost).toHaveBeenCalledWith('/api/v1/knowledge/query', {
        query: 'test query',
      });
      expect(result).toEqual(mockResponse);
    });
  });
});
