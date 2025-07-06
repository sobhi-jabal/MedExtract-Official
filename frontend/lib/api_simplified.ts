/**
 * Simplified API client for direct extraction without job management
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  maxContentLength: 500 * 1024 * 1024, // 500MB
  maxBodyLength: 500 * 1024 * 1024,    // 500MB
  timeout: 300000, // 5 minutes timeout for large files
});

// Types
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: Record<string, boolean>;
  llm_status: any;
  active_jobs: number;
  version: string;
}

export interface ModelInfo {
  available_models: string[];
  default_model: string;
  model_info: Record<string, any>;
}

export interface DatapointConfig {
  name: string;
  instruction: string;
  query?: string;
  default_value?: string;
  valid_values?: string[];
  few_shots?: Array<{ role: string; content: string }>;
}

export interface ExtractionConfig {
  text_column: string;
  ground_truth_column?: string;
  datapoint_configs: DatapointConfig[];
  llm_model: string;
  use_rag: boolean;
  temperature: number;
  top_k?: number;
  top_p?: number;
  num_ctx?: number;
  extraction_strategy: 'single_call' | 'multi_call';
  chunk_size?: number;
  chunk_overlap?: number;
  retriever_type?: string;
  reranker_top_n?: number;
  use_few_shots?: boolean;
  batch_size?: number;
  save_intermediate?: boolean;
  save_frequency?: number;
  store_metadata?: boolean;
  output_directory?: string;
}

export interface ExtractionResult {
  session_id: string;
  status: string;
  rows_processed: number;
  datapoints_extracted: string[];
  metrics?: Record<string, any>;
  download_url: string;
}

export interface ExtractionProgress {
  session_id: string;
  status: string;
  current_row: number;
  total_rows: number;
  percentage: number;
  message?: string;
  error?: string;
}

export interface ConfigPreset {
  id: string;
  name: string;
  description: string;
  datapoints: number;
}

export interface FilePreview {
  columns: string[];
  rows: any[];
  total_rows: number;
}

// API functions
export const healthAPI = {
  check: async (): Promise<HealthStatus> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export const modelsAPI = {
  list: async (): Promise<ModelInfo> => {
    const response = await apiClient.get('/models');
    return response.data;
  },
  
  pull: async (modelName: string): Promise<{ status: string; message: string; model_name: string }> => {
    const response = await apiClient.post('/models/pull', { model_name: modelName });
    return response.data;
  },
  
  delete: async (modelName: string): Promise<{ status: string; message: string; model_name: string }> => {
    const response = await apiClient.delete(`/models/${encodeURIComponent(modelName)}`);
    return response.data;
  },
};

export const presetsAPI = {
  list: async (): Promise<{ presets: ConfigPreset[] }> => {
    const response = await apiClient.get('/presets');
    return response.data;
  },
  
  get: async (presetId: string): Promise<any> => {
    const response = await apiClient.get(`/presets/${presetId}`);
    return response.data;
  },
};

export const extractionAPI = {
  preview: async (file: File): Promise<FilePreview> => {
    console.log('Uploading file for preview:', {
      name: file.name,
      size: file.size,
      type: file.type,
    });
    
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('API Base URL:', API_BASE_URL);
    console.log('Preview endpoint:', `${API_BASE_URL}/preview`);
    
    try {
      const response = await apiClient.post('/preview', formData);
      console.log('Preview response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Preview API error:', error);
      throw error;
    }
  },
  
  start: async (file: File, config: ExtractionConfig): Promise<ExtractionResult> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('config', JSON.stringify(config));
      
      console.log('Sending extraction request with config:', config);
      
      const response = await apiClient.post('/extract', formData);
      console.log('Extraction response:', response.data);
      
      return response.data;
    } catch (error: any) {
      console.error('Extraction API error:', error);
      console.error('Error response:', error.response?.data);
      throw error;
    }
  },
  
  getProgress: async (sessionId: string): Promise<ExtractionProgress> => {
    const response = await apiClient.get(`/extract/${sessionId}/progress`);
    return response.data;
  },
  
  getResults: async (sessionId: string): Promise<any> => {
    const response = await apiClient.get(`/extract/${sessionId}/results`);
    return response.data;
  },
  
  stop: async (sessionId: string): Promise<any> => {
    const response = await apiClient.post(`/extract/${sessionId}/stop`);
    return response.data;
  },
  
  download: async (sessionId: string, format: 'csv' | 'excel' = 'csv'): Promise<Blob> => {
    const response = await apiClient.get(`/extract/${sessionId}/download`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },
};

// WebSocket for real-time progress
export const createProgressWebSocket = (sessionId: string, onMessage: (data: any) => void): WebSocket => {
  const wsUrl = API_BASE_URL.replace(/^http/, 'ws');
  const ws = new WebSocket(`${wsUrl}/ws/progress/${sessionId}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  return ws;
};

// Utility functions
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default apiClient;