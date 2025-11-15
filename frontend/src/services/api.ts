import axios, { AxiosInstance } from 'axios';
import { DocumentMetadata, AnalysisResult, AnalysisStatus } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  setAuthToken(token: string) {
    this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  removeAuthToken() {
    delete this.api.defaults.headers.common['Authorization'];
  }

  // Document endpoints
  async uploadDocument(file: File): Promise<DocumentMetadata> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getDocumentMetadata(documentId: string): Promise<DocumentMetadata> {
    const response = await this.api.get(`/documents/${documentId}`);
    return response.data;
  }

  async listDocuments(skip = 0, limit = 10): Promise<DocumentMetadata[]> {
    const response = await this.api.get('/documents', {
      params: { skip, limit },
    });
    return response.data;
  }

  async deleteDocument(documentId: string): Promise<void> {
    await this.api.delete(`/documents/${documentId}`);
  }

  // Analysis endpoints
  async createAnalysis(
    documentId: string,
    useSentenceTokenizer = true
  ): Promise<AnalysisStatus> {
    const response = await this.api.post('/analysis', {
      document_id: documentId,
      use_sentence_tokenizer: useSentenceTokenizer,
    });
    return response.data;
  }

  async getAnalysisResult(analysisId: string): Promise<AnalysisResult> {
    const response = await this.api.get(`/analysis/${analysisId}`);
    return response.data;
  }

  async getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
    const response = await this.api.get(`/analysis/${analysisId}/status`);
    return response.data;
  }

  async getDocumentAnalyses(documentId: string): Promise<AnalysisResult[]> {
    const response = await this.api.get(`/analysis/document/${documentId}`);
    return response.data;
  }

  async listUserAnalyses(page = 1, pageSize = 10): Promise<any> {
    const response = await this.api.get('/analysis', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  // Health endpoints
  async healthCheck(): Promise<any> {
    const response = await this.api.get('/health');
    return response.data;
  }
}

export const apiService = new ApiService();
