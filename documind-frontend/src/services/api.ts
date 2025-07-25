import axios from 'axios';

// Update the API_BASE configuration for production
const API_BASE = process.env.NODE_ENV === 'production' 
  ? process.env.REACT_APP_API_URL || 'https://documind-backend-700575219498.us-central1.run.app'
  : process.env.REACT_APP_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Request interceptor for logging
apiClient.interceptors.request.use((config) => {
  console.log(`🔄 ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Add better error handling for production
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Add retry logic for production
    if (error.response?.status >= 500 && !error.config._retry) {
      error.config._retry = true;
      console.log('🔄 Retrying request due to server error...');
      await new Promise(resolve => setTimeout(resolve, 1000));
      return apiClient.request(error.config);
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
  upload: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
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
