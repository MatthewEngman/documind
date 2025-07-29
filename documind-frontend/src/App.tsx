import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import UnifiedDashboard from './components/UnifiedDashboard';
import { PerformanceMetrics } from './components/PerformanceMetrics';
import { RedisChallenge } from './components/RedisChallenge';
import CompetitionBanner from './components/CompetitionBanner';
import { Document, SearchResult } from './services/api';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [selectedSearchResult, setSelectedSearchResult] = useState<SearchResult | null>(null);
  const [redisStatus, setRedisStatus] = useState<'connected' | 'disconnected' | 'loading'>('loading');

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDocumentSelect = (doc: Document) => {
    setSelectedDocument(doc);
    console.log('Selected document:', doc);
  };

  const handleSearchResultClick = (result: SearchResult) => {
    setSelectedSearchResult(result);
    console.log('Selected search result:', result);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <Layout>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <CompetitionBanner />
            <UnifiedDashboard 
              refreshTrigger={refreshTrigger}
              onUploadSuccess={handleUploadSuccess}
              onDocumentSelect={handleDocumentSelect}
              onSearchResultClick={handleSearchResultClick}
            />
            <PerformanceMetrics />
            <RedisChallenge />
          </div>
        </Layout>
        
        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </QueryClientProvider>
  );
}

export default App;
