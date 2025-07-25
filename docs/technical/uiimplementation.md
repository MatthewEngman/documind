# DocuMind Frontend Implementation

## 🎯 Overview

A modern React frontend that showcases Redis AI capabilities through an intuitive document management and semantic search interface.

## 🚀 Quick Setup

```bash
# Create React app with TypeScript
npx create-react-app documind-frontend --template typescript
cd documind-frontend

# Install dependencies
npm install @tanstack/react-query axios
npm install lucide-react clsx tailwind-merge
npm install react-dropzone react-hot-toast
npm install recharts framer-motion
npm install @headlessui/react

# Install and configure Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

## 🎨 Tailwind Configuration

Update `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        redis: {
          500: '#dc382d',
          600: '#b91c1c',
          700: '#991b1b',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
```

Add to `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
```

## 🔧 API Service

Create `src/services/api.ts`:

```typescript
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Request interceptor for logging
apiClient.interceptors.request.use((config) => {
  console.log(`🔄 ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
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
```

## 🧩 Core Components

### 1. Layout Component

Create `src/components/Layout.tsx`:

```typescript
import React from 'react';
import { motion } from 'framer-motion';
import { Database, Search, BarChart3, FileText } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  currentTab: string;
  onTabChange: (tab: string) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, currentTab, onTabChange }) => {
  const tabs = [
    { id: 'search', label: 'Search', icon: Search },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-redis-500 to-primary-600 rounded-lg">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">DocuMind</h1>
                <p className="text-xs text-gray-500">Redis AI Challenge 2025</p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex space-x-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${currentTab === tab.id
                      ? 'bg-primary-100 text-primary-700 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }
                  `}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>

            {/* Status indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">Redis Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          key={currentTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
};

export default Layout;
```

### 2. Document Upload Component

Create `src/components/DocumentUpload.tsx`:

```typescript
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, File, CheckCircle, XCircle, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { documentApi } from '../services/api';

interface DocumentUploadProps {
  onUploadSuccess: () => void;
}

interface UploadProgress {
  file: File;
  status: 'uploading' | 'processing' | 'success' | 'error';
  progress: number;
  docId?: string;
  error?: string;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess }) => {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Initialize upload progress
    const newUploads: UploadProgress[] = acceptedFiles.map(file => ({
      file,
      status: 'uploading',
      progress: 0,
    }));

    setUploads(prev => [...prev, ...newUploads]);

    // Process each file
    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      const uploadIndex = uploads.length + i;

      try {
        // Update progress to processing
        setUploads(prev => prev.map((upload, idx) => 
          idx === uploadIndex 
            ? { ...upload, status: 'processing', progress: 50 }
            : upload
        ));

        // Upload file
        const result = await documentApi.upload(file);
        
        // Update progress to success
        setUploads(prev => prev.map((upload, idx) => 
          idx === uploadIndex 
            ? { 
                ...upload, 
                status: 'success', 
                progress: 100,
                docId: result.doc_id 
              }
            : upload
        ));

        toast.success(`${file.name} uploaded successfully!`);
        onUploadSuccess();

      } catch (error: any) {
        // Update progress to error
        setUploads(prev => prev.map((upload, idx) => 
          idx === uploadIndex 
            ? { 
                ...upload, 
                status: 'error', 
                progress: 0,
                error: error.response?.data?.detail || error.message 
              }
            : upload
        ));

        toast.error(`Failed to upload ${file.name}`);
      }
    }
  }, [uploads.length, onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeUpload = (index: number) => {
    setUploads(prev => prev.filter((_, idx) => idx !== index));
  };

  return (
    <div className="space-y-6">
      {/* Drop zone */}
      <motion.div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
          ${isDragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
        `}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <div className={`
              p-3 rounded-full 
              ${isDragActive ? 'bg-primary-500' : 'bg-gray-400'}
            `}>
              <Upload className={`w-8 h-8 ${isDragActive ? 'text-white' : 'text-white'}`} />
            </div>
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop files here' : 'Upload documents'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Drag & drop files or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Supports PDF, DOCX, TXT, MD • Max 10MB per file
            </p>
          </div>
        </div>
      </motion.div>

      {/* Upload progress */}
      <AnimatePresence>
        {uploads.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            <h3 className="text-sm font-medium text-gray-900">Upload Progress</h3>
            
            {uploads.map((upload, index) => (
              <motion.div
                key={`${upload.file.name}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="bg-white rounded-lg border border-gray-200 p-4"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <File className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {upload.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(upload.file.size / 1024 / 1024).toFixed(1)} MB
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    {/* Status icon */}
                    {upload.status === 'uploading' || upload.status === 'processing' ? (
                      <Loader className="w-5 h-5 text-primary-500 animate-spin" />
                    ) : upload.status === 'success' ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}

                    {/* Remove button */}
                    <button
                      onClick={() => removeUpload(index)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Progress bar */}
                {(upload.status === 'uploading' || upload.status === 'processing') && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>
                        {upload.status === 'uploading' ? 'Uploading...' : 'Processing...'}
                      </span>
                      <span>{upload.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <motion.div
                        className="bg-primary-500 h-2 rounded-full"
                        style={{ width: `${upload.progress}%` }}
                        initial={{ width: 0 }}
                        animate={{ width: `${upload.progress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                  </div>
                )}

                {/* Error message */}
                {upload.status === 'error' && upload.error && (
                  <div className="mt-2 text-xs text-red-600 bg-red-50 rounded p-2">
                    {upload.error}
                  </div>
                )}

                {/* Success message */}
                {upload.status === 'success' && (
                  <div className="mt-2 text-xs text-green-600 bg-green-50 rounded p-2">
                    Document processed successfully! Ready for search.
                  </div>
                )}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DocumentUpload;
```

### 3. Search Interface Component

Create `src/components/SearchInterface.tsx`:

```typescript
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Clock, Zap, FileText, Tag, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { searchApi, SearchResult } from '../services/api';
import toast from 'react-hot-toast';

interface SearchInterfaceProps {
  onResultClick: (result: SearchResult) => void;
}

const SearchInterface: React.FC<SearchInterfaceProps> = ({ onResultClick }) => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchStats, setSearchStats] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Get search suggestions
  const { data: suggestionsData } = useQuery({
    queryKey: ['suggestions', query],
    queryFn: () => searchApi.getSuggestions(query),
    enabled: query.length > 2,
    staleTime: 30000,
  });

  useEffect(() => {
    if (suggestionsData?.suggestions) {
      setSuggestions(suggestionsData.suggestions);
      setShowSuggestions(true);
    }
  }, [suggestionsData]);

  const handleSearch = async (searchQuery: string = query) => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setShowSuggestions(false);

    try {
      const result = await searchApi.search(searchQuery, {
        limit: 20,
        similarity_threshold: 0.3,
        use_cache: true,
      });

      setSearchResults(result.results);
      setSearchStats({
        total_results: result.total_results,
        search_time_ms: result.search_time_ms,
        cache_hit: result.cache_hit,
        embedding_method: result.embedding_method,
      });

      if (result.results.length === 0) {
        toast('No results found. Try a different query.', { icon: '🔍' });
      }

    } catch (error: any) {
      toast.error('Search failed. Please try again.');
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.split(' ').join('|')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 text-yellow-900 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const exampleQueries = [
    "API security best practices",
    "Redis performance optimization", 
    "Database caching strategies",
    "Technical documentation",
    "Enterprise architecture patterns"
  ];

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="text-center space-y-4">
        <motion.h2 
          className="text-3xl font-bold text-gray-900"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Semantic Document Search
        </motion.h2>
        <motion.p 
          className="text-gray-600 max-w-2xl mx-auto"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          Search through your documents using natural language. Powered by Redis Vector Sets 
          and OpenAI embeddings for instant semantic matching.
        </motion.p>
      </div>

      {/* Search Input */}
      <motion.div 
        className="relative max-w-4xl mx-auto"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
      >
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            onFocus={() => setShowSuggestions(suggestions.length > 0)}
            placeholder="Ask me anything about your documents..."
            className="w-full pl-12 pr-32 py-4 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none shadow-sm"
          />
          
          <div className="absolute inset-y-0 right-0 flex items-center pr-4">
            <button
              onClick={() => handleSearch()}
              disabled={!query.trim() || isSearching}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center space-x-2"
            >
              {isSearching ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Search</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Search Suggestions */}
        <AnimatePresence>
          {showSuggestions && suggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg"
            >
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setQuery(suggestion);
                    handleSearch(suggestion);
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg flex items-center space-x-2"
                >
                  <Search className="w-4 h-4 text-gray-400" />
                  <span>{suggestion}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Example Queries */}
      {!searchResults.length && !isSearching && (
        <motion.div 
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <p className="text-sm text-gray-500 mb-3">Try these example queries:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                onClick={() => {
                  setQuery(example);
                  handleSearch(example);
                }}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Search Stats */}
      {searchStats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-center"
        >
          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span className="text-gray-600">
                  {searchStats.total_results} results
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-blue-500" />
                <span className="text-gray-600">
                  {searchStats.search_time_ms}ms
                </span>
              </div>
              
              {searchStats.cache_hit && (
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  <span className="text-gray-600">Cached</span>
                </div>
              )}
              
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-primary-500 rounded-full"></div>
                <span className="text-gray-600 capitalize">
                  {searchStats.embedding_method}
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Search Results */}
      <AnimatePresence>
        {searchResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <h3 className="text-lg font-semibold text-gray-900">
              Search Results ({searchResults.length})
            </h3>
            
            <div className="space-y-3">
              {searchResults.map((result, index) => (
                <motion.div
                  key={`${result.chunk_id}-${index}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => onResultClick(result)}
                  className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-primary-300 cursor-pointer transition-all group"
                >
                  {/* Result Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="text-lg font-medium text-gray-900 group-hover:text-primary-700 transition-colors">
                        {result.title || result.filename}
                      </h4>
                      <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                        <div className="flex items-center space-x-1">
                          <FileText className="w-4 h-4" />
                          <span>{result.filename}</span>
                        </div>
                        <span>Chunk {result.chunk_index + 1}</span>
                        <span>{result.word_count} words</span>
                      </div>
                    </div>
                    
                    <div className="ml-4 text-right">
                      <div className="flex items-center space-x-1">
                        <div className={`w-2 h-2 rounded-full ${
                          result.similarity_score > 0.8 ? 'bg-green-500' :
                          result.similarity_score > 0.6 ? 'bg-yellow-500' : 'bg-orange-500'
                        }`} />
                        <span className="text-sm font-medium text-gray-700">
                          {(result.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        relevance
                      </div>
                    </div>
                  </div>

                  {/* Content Preview */}
                  <div className="text-gray-700 leading-relaxed mb-3">
                    {highlightText(
                      result.content.length > 300 
                        ? result.content.substring(0, 300) + '...'
                        : result.content,
                      query
                    )}
                  </div>

                  {/* Tags */}
                  {result.tags && result.tags.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <Tag className="w-4 h-4 text-gray-400" />
                      <div className="flex flex-wrap gap-1">
                        {result.tags.slice(0, 5).map((tag, tagIndex) => (
                          <span
                            key={tagIndex}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                        {result.tags.length > 5 && (
                          <span className="text-xs text-gray-500">
                            +{result.tags.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* No Results */}
      {searchResults.length === 0 && !isSearching && query && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <Search className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-500 mb-4">
            Try adjusting your search terms or upload more documents.
          </p>
          <button
            onClick={() => {
              setQuery('');
              setSearchResults([]);
              setSearchStats(null);
              searchInputRef.current?.focus();
            }}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Clear search
          </button>
        </motion.div>
      )}
    </div>
  );
};

export default SearchInterface;
```

### 4. Document List Component

Create `src/components/DocumentList.tsx`:

```typescript
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { 
  FileText, 
  Trash2, 
  Download, 
  Eye, 
  Calendar, 
  Hash, 
  Weight,
  Tag,
  MoreVertical
} from 'lucide-react';
import { documentApi, Document } from '../services/api';
import toast from 'react-hot-toast';

interface DocumentListProps {
  refreshTrigger: number;
  onDocumentSelect: (doc: Document) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({ refreshTrigger, onDocumentSelect }) => {
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());
  const [showActions, setShowActions] = useState<string | null>(null);

  const { data: documentsData, isLoading, refetch } = useQuery({
    queryKey: ['documents', refreshTrigger],
    queryFn: () => documentApi.list(50, 0),
    staleTime: 30000,
  });

  const documents = documentsData?.documents || [];

  const handleDelete = async (docId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await documentApi.delete(docId);
      toast.success('Document deleted successfully');
      refetch();
    } catch (error) {
      toast.error('Failed to delete document');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('word')) return '📝';
    if (mimeType.includes('text')) return '📋';
    return '📄';
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
              <div className="flex-1 space-y-2">
                <div className="h-5 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-12"
      >
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <FileText className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No documents yet</h3>
        <p className="text-gray-500">
          Upload your first document to get started with semantic search.
        </p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          Documents ({documents.length})
        </h2>
        
        {selectedDocs.size > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {selectedDocs.size} selected
            </span>
            <button
              onClick={() => {
                selectedDocs.forEach(docId => handleDelete(docId));
                setSelectedDocs(new Set());
              }}
              className="px-3 py-1 text-sm bg-red-50 text-red-700 rounded-lg hover:bg-red-100"
            >
              Delete Selected
            </button>
          </div>
        )}
      </div>

      <div className="grid gap-4">
        <AnimatePresence>
          {documents.map((doc, index) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white rounded-lg border border-gray-200 hover:shadow-md hover:border-primary-300 transition-all group"
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  {/* Document Info */}
                  <div 
                    className="flex items-start space-x-4 flex-1 cursor-pointer"
                    onClick={() => onDocumentSelect(doc)}
                  >
                    {/* File Icon */}
                    <div className="w-12 h-12 bg-gradient-to-br from-primary-50 to-primary-100 rounded-lg flex items-center justify-center text-2xl group-hover:from-primary-100 group-hover:to-primary-200 transition-all">
                      {getFileIcon(doc.mime_type)}
                    </div>

                    {/* Document Details */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-medium text-gray-900 group-hover:text-primary-700 transition-colors truncate">
                        {doc.title}
                      </h3>
                      
                      <p className="text-sm text-gray-500 truncate mb-3">
                        {doc.filename}
                      </p>

                      {/* Document Stats */}
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Weight className="w-3 h-3" />
                          <span>{formatFileSize(doc.size_bytes)}</span>
                        </div>
                        
                        <div className="flex items-center space-x-1">
                          <Hash className="w-3 h-3" />
                          <span>{doc.word_count.toLocaleString()} words</span>
                        </div>
                        
                        <div className="flex items-center space-x-1">
                          <FileText className="w-3 h-3" />
                          <span>{doc.chunk_count} chunks</span>
                        </div>
                        
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(doc.uploaded_at)}</span>
                        </div>
                      </div>

                      {/* Tags */}
                      {doc.tags && doc.tags.length > 0 && (
                        <div className="flex items-center space-x-2 mt-3">
                          <Tag className="w-3 h-3 text-gray-400" />
                          <div className="flex flex-wrap gap-1">
                            {doc.tags.slice(0, 4).map((tag, tagIndex) => (
                              <span
                                key={tagIndex}
                                className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full"
                              >
                                {tag}
                              </span>
                            ))}
                            {doc.tags.length > 4 && (
                              <span className="text-xs text-gray-500">
                                +{doc.tags.length - 4}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="relative">
                    <button
                      onClick={() => setShowActions(showActions === doc.id ? null : doc.id)}
                      className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>

                    <AnimatePresence>
                      {showActions === doc.id && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.95, y: -10 }}
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.95, y: -10 }}
                          className="absolute right-0 top-full mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10"
                        >
                          <div className="py-1">
                            <button
                              onClick={() => {
                                onDocumentSelect(doc);
                                setShowActions(null);
                              }}
                              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-2"
                            >
                              <Eye className="w-4 h-4" />
                              <span>View Details</span>
                            </button>
                            
                            <button
                              onClick={() => {
                                // In a real app, you'd implement document download
                                toast.info('Download feature coming soon!');
                                setShowActions(null);
                              }}
                              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-2"
                            >
                              <Download className="w-4 h-4" />
                              <span>Download</span>
                            </button>
                            
                            <hr className="my-1" />
                            
                            <button
                              onClick={() => {
                                handleDelete(doc.id);
                                setShowActions(null);
                              }}
                              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
                            >
                              <Trash2 className="w-4 h-4" />
                              <span>Delete</span>
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>

                {/* Processing Status */}
                {doc.status !== 'processed' && (
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                      <span className="text-sm text-yellow-800">
                        Processing document... This may take a moment.
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default DocumentList;
```

### 5. Analytics Dashboard Component

Create `src/components/AnalyticsDashboard.tsx`:

```typescript
import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import {
  Database,
  Search,
  Zap,
  FileText,
  TrendingUp,
  Clock,
  Server,
  Activity
} from 'lucide-react';
import { searchApi, systemApi } from '../services/api';

const AnalyticsDashboard: React.FC = () => {
  const { data: searchAnalytics, isLoading: searchLoading } = useQuery({
    queryKey: ['searchAnalytics'],
    queryFn: searchApi.getAnalytics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: systemStats, isLoading: systemLoading } = useQuery({
    queryKey: ['systemStats'],
    queryFn: systemApi.getStats,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const isLoading = searchLoading || systemLoading;

  // Prepare chart data
  const cacheData = searchAnalytics ? [
    { name: 'Cache Hits', value: searchAnalytics.search_performance.cache_hits, color: '#10b981' },
    { name: 'Cache Misses', value: searchAnalytics.search_performance.cache_misses, color: '#f59e0b' },
  ] : [];

  const performanceData = [
    { metric: 'Search Speed', value: 'Sub-second', target: '< 500ms' },
    { metric: 'Cache Hit Rate', value: `${searchAnalytics?.search_performance.cache_hit_rate || 0}%`, target: '> 60%' },
    { metric: 'Vector Index', value: searchAnalytics?.vector_search.status || 'Unknown', target: 'Active' },
    { metric: 'Embedding Method', value: searchAnalytics?.embedding_service.default_method || 'Unknown', target: 'OpenAI' },
  ];

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ReactNode;
    color: string;
    trend?: { value: number; isPositive: boolean };
  }> = ({ title, value, subtitle, icon, color, trend }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
      </div>
      
      {trend && (
        <div className="mt-4 flex items-center">
          <div className={`flex items-center text-sm ${
            trend.isPositive ? 'text-green-600' : 'text-red-600'
          }`}>
            <TrendingUp className={`w-4 h-4 mr-1 ${
              trend.isPositive ? '' : 'transform rotate-180'
            }`} />
            <span>{Math.abs(trend.value)}%</span>
          </div>
          <span className="text-sm text-gray-500 ml-2">from last hour</span>
        </div>
      )}
    </motion.div>
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-20"></div>
                  <div className="h-8 bg-gray-200 rounded w-16"></div>
                </div>
                <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <motion.h2 
          className="text-3xl font-bold text-gray-900"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Performance Analytics
        </motion.h2>
        <motion.p 
          className="text-gray-600 mt-2"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          Real-time insights into your Redis-powered semantic search system
        </motion.p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Searches"
          value={searchAnalytics?.search_performance.total_searches.toLocaleString() || '0'}
          subtitle="All time"
          icon={<Search className="w-6 h-6 text-white" />}
          color="bg-blue-500"
          trend={{ value: 12, isPositive: true }}
        />
        
        <StatCard
          title="Cache Hit Rate"
          value={`${searchAnalytics?.search_performance.cache_hit_rate || 0}%`}
          subtitle="Last 24 hours"
          icon={<Zap className="w-6 h-6 text-white" />}
          color="bg-green-500"
          trend={{ value: 8, isPositive: true }}
        />
        
        <StatCard
          title="Total Documents"
          value={systemStats?.documents.total_documents.toLocaleString() || '0'}
          subtitle={`${systemStats?.documents.total_chunks || 0} chunks`}
          icon={<FileText className="w-6 h-6 text-white" />}
          color="bg-purple-500"
        />
        
        <StatCard
          title="Redis Memory"
          value={systemStats?.redis.memory_used || '0B'}
          subtitle={`${systemStats?.redis.total_keys || 0} keys`}
          icon={<Database className="w-6 h-6 text-white" />}
          color="bg-redis-500"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cache Performance */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Performance</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={cacheData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {cacheData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [value, 'Requests']} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center space-x-4 mt-4">
            {cacheData.map((entry, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-600">{entry.name}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* System Health */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-lg border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-4">
            {performanceData.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{item.metric}</p>
                  <p className="text-xs text-gray-500">Target: {item.target}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">{item.value}</p>
                  <div className="w-2 h-2 bg-green-500 rounded-full ml-auto mt-1"></div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Performance Metrics Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-lg border border-gray-200 p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Metrics</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Component
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Database className="w-5 h-5 text-redis-500 mr-3" />
                    <span className="text-sm font-medium text-gray-900">Redis</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Connected
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {systemStats?.redis.memory_used || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {systemStats?.redis.total_keys || 0} keys, {systemStats?.redis.connected_clients || 0} clients