import axios from 'axios';

// Update the API_BASE configuration for production
const API_BASE = process.env.NODE_ENV === 'production' 
  ? process.env.REACT_APP_API_URL || 'https://documind-backend-700575219498.us-central1.run.app'
  : process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    const config = error.config;
    
    // Add retry logic for network errors and server errors
    if ((error.response?.status >= 500 || error.code === 'NETWORK_ERROR') && !config._retry) {
      config._retry = true;
      config._retryCount = (config._retryCount || 0) + 1;
      
      if (config._retryCount <= 3) {
        console.log(`🔄 Retrying request (${config._retryCount}/3) due to ${error.response?.status || error.code}...`);
        
        const delay = Math.min(1000 * Math.pow(2, config._retryCount - 1), 5000);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        return apiClient.request(config);
      }
    }
    
    console.error('❌ API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface Document {
  id: string;
  title: string;
  filename: string;
  size_bytes: number;
  word_count: number;
  chunk_count: number;
  uploaded_at: string;
  processed_at: string;
  tags: string[];
  status: string;
  mime_type: string;
}

export interface SearchResult {
  chunk_id: string;
  doc_id: string;
  content: string;
  title: string;
  filename: string;
  similarity_score: number;
  word_count: number;
  chunk_index: number;
  tags: string[];
  upload_date: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
  cache_hit: boolean;
  embedding_method: string;
}

export interface SystemStats {
  system: {
    status: string;
    redis_connected: boolean;
  };
  redis: {
    memory_used: string;
    total_keys: number;
    connected_clients: number;
    total_commands: number;
  };
  documents: {
    total_documents: number;
    processed_documents: number;
    total_chunks: number;
  };
}

export interface SearchAnalytics {
  search_performance: {
    total_searches: number;
    cache_hits: number;
    cache_misses: number;
    cache_hit_rate: number;
  };
  vector_search: {
    status: string;
    total_docs: number;
    total_vectors: number;
  };
  embedding_service: {
    cache_size: number;
    openai_available: boolean;
    local_model_available: boolean;
    default_method: string;
  };
}

// Document API
export const documentApi = {
  upload: async (file: File, onProgress?: (progress: number) => void): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    
    // Calculate dynamic timeout based on file size (minimum 2 minutes, +30s per MB)
    const fileSizeMB = file.size / (1024 * 1024);
    const dynamicTimeout = Math.max(120000, 120000 + (fileSizeMB * 30000)); // 2min base + 30s per MB
    
    const response = await apiClient.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: dynamicTimeout,
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  list: async (limit = 20, offset = 0): Promise<{ documents: Document[]; total: number }> => {
    const response = await apiClient.get(`/api/documents/?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  get: async (docId: string): Promise<Document> => {
    const response = await apiClient.get(`/api/documents/${docId}`);
    return response.data;
  },

  delete: async (docId: string): Promise<void> => {
    await apiClient.delete(`/api/documents/${docId}`);
  },

  getChunks: async (docId: string, limit = 10, offset = 0) => {
    const response = await apiClient.get(`/api/documents/${docId}/chunks?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  getStatus: async (docId: string) => {
    const response = await apiClient.get(`/api/documents/${docId}/status`);
    return response.data;
  },

  batchUpload: async (files: File[]): Promise<any> => {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append('files', file);
    });
    
    const response = await apiClient.post('/api/documents/batch-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000,
    });
    return response.data;
  },
};

// Search API
export const searchApi = {
  search: async (query: string, options: {
    limit?: number;
    similarity_threshold?: number;
    filters?: any;
    use_cache?: boolean;
  } = {}): Promise<SearchResponse> => {
    const response = await apiClient.post('/api/search/', {
      query,
      limit: options.limit || 10,
      similarity_threshold: options.similarity_threshold || 0.7,
      filters: options.filters,
      use_cache: options.use_cache !== false,
    });
    return response.data;
  },

  getSuggestions: async (query: string): Promise<{ suggestions: string[] }> => {
    const response = await apiClient.get(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  getAnalytics: async (): Promise<SearchAnalytics> => {
    const response = await apiClient.get('/api/search/analytics');
    return response.data;
  },
};

// System API
export const systemApi = {
  getHealth: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  getStats: async (): Promise<SystemStats> => {
    const response = await apiClient.get('/api/system/stats');
    return response.data;
  },
};

export default apiClient;
