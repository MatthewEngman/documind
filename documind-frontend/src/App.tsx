import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import DocumentUpload from './components/DocumentUpload';
import SearchInterface from './components/SearchInterface';
import DocumentList from './components/DocumentList';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import { RedisShowcase } from './components/RedisShowcase';
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
  const [activeTab, setActiveTab] = useState<string>('upload');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [selectedSearchResult, setSelectedSearchResult] = useState<SearchResult | null>(null);
  const [redisStatus, setRedisStatus] = useState<'connected' | 'disconnected' | 'loading'>('loading');

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
    // Optionally switch to documents tab after upload
    // setActiveTab('documents');
  };

  const handleDocumentSelect = (doc: Document) => {
    setSelectedDocument(doc);
    // You could open a modal or navigate to a detail view here
    console.log('Selected document:', doc);
  };

  const handleSearchResultClick = (result: SearchResult) => {
    setSelectedSearchResult(result);
    // You could highlight the relevant document or open a detail view
    console.log('Selected search result:', result);
  };

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'upload':
        return <DocumentUpload onUploadSuccess={handleUploadSuccess} />;
      
      case 'search':
        return <SearchInterface onResultClick={handleSearchResultClick} />;
      
      case 'documents':
        return (
          <DocumentList 
            refreshTrigger={refreshTrigger}
            onDocumentSelect={handleDocumentSelect}
          />
        );
      
      case 'analytics':
        return <AnalyticsDashboard />;
      
      default:
        return <DocumentUpload onUploadSuccess={handleUploadSuccess} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <Layout activeTab={activeTab} onTabChange={setActiveTab}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <CompetitionBanner />
            <RedisShowcase />
            <PerformanceMetrics />
            <RedisChallenge />
            {renderActiveTab()}
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
