import axios, { AxiosResponse } from 'axios';
import type {
  KnowledgeSearchRequest,
  KnowledgeSearchResult,
  DocumentUploadRequest,
  DocumentUploadResponse,
  KnowledgeStatistics,
} from '../types/knowledge';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class KnowledgeApiClient {
  private baseURL: string;

  constructor() {
    this.baseURL = `${BASE_URL}/api/v1/knowledge`;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {};

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  }

  async query(request: KnowledgeSearchRequest, collection: string = 'default'): Promise<KnowledgeSearchResult[]> {
    const response: AxiosResponse<KnowledgeSearchResult[]> = await axios.post(
      `${this.baseURL}/query`,
      request,
      {
        params: { collection },
        headers: {
          ...this.getAuthHeaders(),
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  }

  async uploadDocument(uploadRequest: DocumentUploadRequest): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', uploadRequest.file);
    formData.append('category', uploadRequest.category);

    if (uploadRequest.technology_id !== undefined) {
      formData.append('technology_id', uploadRequest.technology_id.toString());
    }

    if (uploadRequest.collection) {
      formData.append('collection', uploadRequest.collection);
    } else {
      formData.append('collection', 'default');
    }

    const response: AxiosResponse<DocumentUploadResponse> = await axios.post(
      `${this.baseURL}/documents`,
      formData,
      {
        headers: {
          ...this.getAuthHeaders(),
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async deleteDocument(id: number, collection: string = 'default'): Promise<void> {
    await axios.delete(
      `${this.baseURL}/documents/${id}`,
      {
        params: { collection },
        headers: this.getAuthHeaders(),
      }
    );
  }

  async getStatistics(collection: string = 'default'): Promise<KnowledgeStatistics> {
    const response: AxiosResponse<KnowledgeStatistics> = await axios.get(
      `${this.baseURL}/statistics`,
      {
        params: { collection },
        headers: this.getAuthHeaders(),
      }
    );
    return response.data;
  }

  async getCollections(): Promise<string[]> {
    const response: AxiosResponse<string[]> = await axios.get(
      `${this.baseURL}/collections`,
      {
        headers: this.getAuthHeaders(),
      }
    );
    return response.data;
  }

  async getCategories(collection: string = 'default'): Promise<string[]> {
    const response: AxiosResponse<string[]> = await axios.get(
      `${this.baseURL}/categories`,
      {
        params: { collection },
        headers: this.getAuthHeaders(),
      }
    );
    return response.data;
  }
}

export const knowledgeApi = new KnowledgeApiClient();
export default knowledgeApi;
