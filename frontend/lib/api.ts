import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API Types
export interface Job {
  job_id: string
  name: string
  status: string
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
  progress_percentage: number
  current_step: string
  total_steps: number
  total_rows: number
  processed_rows: number
  successful_rows: number
  failed_rows: number
  error_message?: string
  processing_stats?: Record<string, any>
}

export interface Model {
  name: string
  size: number
  available: boolean
  details: Record<string, any>
}

export interface HealthStatus {
  status: string
  timestamp: string
  components: Record<string, boolean>
  llm_status: Record<string, any>
  active_jobs: number
  version: string
}

export interface DatapointConfig {
  name: string
  prompt: string
  extraction_strategy: string
  output_format: string
  valid_values?: string[]
  use_rag?: boolean
  confidence_threshold?: number
}

export interface ProcessingConfig {
  batch_size: number
  max_workers: number
  timeout_per_item: number
  retry_attempts: number
  save_intermediate: boolean
}

export interface LLMConfig {
  model_name: string
  temperature: number
  max_tokens: number
  top_k: number
  top_p: number
  timeout: number
  max_retries: number
}

export interface RAGConfig {
  enabled: boolean
  strategy: string
  chunk_size: number
  chunk_overlap: number
  top_k: number
  embedding_model: string
  use_reranker: boolean
  reranker_model: string
  reranker_top_n: number
}

export interface JobRequest {
  name: string
  datapoint_configs: DatapointConfig[]
  processing_config: ProcessingConfig
  llm_config?: LLMConfig
  rag_config?: RAGConfig
  text_column: string
  ground_truth_column?: string
}

// API Functions
export const healthAPI = {
  check: (): Promise<HealthStatus> => api.get('/health').then(res => res.data),
}

export const modelsAPI = {
  list: (): Promise<{ available_models: string[], default_model: string, model_info: Record<string, any> }> => 
    api.get('/models').then(res => res.data),
  
  pull: (modelName: string): Promise<{ message: string, success: boolean }> =>
    api.post(`/models/${modelName}/pull`).then(res => res.data),
}

export const jobsAPI = {
  list: (): Promise<Job[]> => api.get('/jobs').then(res => res.data),
  
  get: (jobId: string): Promise<Job> => api.get(`/jobs/${jobId}`).then(res => res.data),
  
  create: (request: JobRequest): Promise<{ job_id: string, status: string, message: string }> =>
    api.post('/jobs', request).then(res => res.data),
  
  start: (jobId: string): Promise<{ message: string, job_id: string }> =>
    api.post(`/jobs/${jobId}/start`).then(res => res.data),
  
  stop: (jobId: string): Promise<{ message: string, job_id: string }> =>
    api.post(`/jobs/${jobId}/stop`).then(res => res.data),
  
  delete: (jobId: string): Promise<{ message: string, job_id: string }> =>
    api.delete(`/jobs/${jobId}`).then(res => res.data),
  
  uploadData: (jobId: string, file: File): Promise<{ message: string, rows: number, columns: string[] }> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/jobs/${jobId}/upload-data`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  
  getResults: (jobId: string): Promise<any> =>
    api.get(`/jobs/${jobId}/results`).then(res => res.data),
  
  downloadResults: (jobId: string, format: 'csv' | 'excel' = 'csv'): Promise<Blob> =>
    api.get(`/jobs/${jobId}/download?format=${format}`, {
      responseType: 'blob',
    }).then(res => res.data),
}

export const configAPI = {
  validate: (config: any): Promise<{ valid: boolean, errors: string[] }> =>
    api.post('/config/validate', config).then(res => res.data),
}

export const systemAPI = {
  cleanup: (daysOld: number = 30): Promise<{ message: string }> =>
    api.post(`/system/cleanup?days_old=${daysOld}`).then(res => res.data),
  
  getDiskUsage: (): Promise<Record<string, number>> =>
    api.get('/system/disk-usage').then(res => res.data),
}

export default api