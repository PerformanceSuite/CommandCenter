import { useState, useCallback } from 'react';
import { knowledgeApi } from '../services/knowledgeApi';
import type {
  KnowledgeSearchRequest,
  KnowledgeSearchResult,
  DocumentUploadRequest,
  KnowledgeStatistics,
} from '../types/knowledge';

export function useKnowledge(initialCollection: string = 'default') {
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[]>([]);
  const [statistics, setStatistics] = useState<KnowledgeStatistics | null>(null);
  const [collections, setCollections] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [currentCollection, setCurrentCollection] = useState(initialCollection);

  const query = useCallback(
    async (request: KnowledgeSearchRequest, collection?: string) => {
      try {
        setLoading(true);
        setError(null);
        const results = await knowledgeApi.query(request, collection || currentCollection);
        setSearchResults(results);
        return results;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to search knowledge base');
        setError(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [currentCollection]
  );

  const uploadDocument = useCallback(
    async (uploadRequest: DocumentUploadRequest) => {
      try {
        setLoading(true);
        setError(null);
        const response = await knowledgeApi.uploadDocument(uploadRequest);
        return response;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to upload document');
        setError(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const deleteDocument = useCallback(
    async (id: number, collection?: string) => {
      try {
        setLoading(true);
        setError(null);
        await knowledgeApi.deleteDocument(id, collection || currentCollection);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to delete document');
        setError(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [currentCollection]
  );

  const fetchStatistics = useCallback(
    async (collection?: string) => {
      try {
        setLoading(true);
        setError(null);
        const stats = await knowledgeApi.getStatistics(collection || currentCollection);
        setStatistics(stats);
        return stats;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to fetch statistics');
        setError(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [currentCollection]
  );

  const fetchCollections = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const colls = await knowledgeApi.getCollections();
      setCollections(colls);
      return colls;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch collections');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchCategories = useCallback(
    async (collection?: string) => {
      try {
        setLoading(true);
        setError(null);
        const cats = await knowledgeApi.getCategories(collection || currentCollection);
        setCategories(cats);
        return cats;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to fetch categories');
        setError(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [currentCollection]
  );

  const clearSearchResults = useCallback(() => {
    setSearchResults([]);
  }, []);

  const switchCollection = useCallback((collection: string) => {
    setCurrentCollection(collection);
    setSearchResults([]);
  }, []);

  return {
    // State
    searchResults,
    statistics,
    collections,
    categories,
    loading,
    error,
    currentCollection,

    // Actions
    query,
    uploadDocument,
    deleteDocument,
    fetchStatistics,
    fetchCollections,
    fetchCategories,
    clearSearchResults,
    switchCollection,
  };
}
