import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, Search, FileText, BarChart3, Database, Zap, Clock, TrendingUp } from 'lucide-react';
import DocumentUpload from './DocumentUpload';
import SearchInterface from './SearchInterface';
import DocumentList from './DocumentList';
import CompactAnalytics from './CompactAnalytics';
import { Document, SearchResult } from '../services/api';

interface UnifiedDashboardProps {
  refreshTrigger: number;
  onUploadSuccess: () => void;
  onDocumentSelect: (doc: Document) => void;
  onSearchResultClick: (result: SearchResult) => void;
}

const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({
  refreshTrigger,
  onUploadSuccess,
  onDocumentSelect,
  onSearchResultClick,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  const handleDocumentSelect = (doc: Document) => {
    setSelectedDocument(doc);
    onDocumentSelect(doc);
  };

  const handleSearchResultClick = (result: SearchResult) => {
    // Highlight the document in the list if it matches
    onSearchResultClick(result);
  };

  return (
    <div className="space-y-6">
      {/* Header Section with Upload */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden"
      >
        <div className="bg-gradient-to-r from-red-500 to-blue-500 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <Upload className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Document Upload</h2>
                <p className="text-white/80 text-sm">Upload documents to start semantic search</p>
              </div>
            </div>
            <div className="flex items-center space-x-4 text-white/80 text-sm">
              <div className="flex items-center space-x-1">
                <Database className="w-4 h-4" />
                <span>Redis Vector Sets</span>
              </div>
              <div className="flex items-center space-x-1">
                <Zap className="w-4 h-4" />
                <span>AI Powered</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <DocumentUpload onUploadSuccess={onUploadSuccess} />
        </div>
      </motion.div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Search & Documents */}
        <div className="lg:col-span-2 space-y-6">
          {/* Search Interface */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden"
          >
            <div className="bg-gradient-to-r from-blue-500 to-purple-500 px-6 py-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white/20 rounded-lg">
                  <Search className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Semantic Search</h2>
                  <p className="text-white/80 text-sm">Search through your documents with AI</p>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              <SearchInterface onResultClick={handleSearchResultClick} />
            </div>
          </motion.div>

          {/* Document List */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden"
          >
            <div className="bg-gradient-to-r from-green-500 to-teal-500 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white/20 rounded-lg">
                    <FileText className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">Document Library</h2>
                    <p className="text-white/80 text-sm">Manage your uploaded documents</p>
                  </div>
                </div>
                <div className="flex items-center space-x-1 text-white/80 text-sm">
                  <Clock className="w-4 h-4" />
                  <span>Real-time</span>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              <DocumentList 
                refreshTrigger={refreshTrigger}
                onDocumentSelect={handleDocumentSelect}
                selectedDocument={selectedDocument}
              />
            </div>
          </motion.div>
        </div>

        {/* Right Column: Analytics */}
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden"
          >
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white/20 rounded-lg">
                  <BarChart3 className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Analytics</h2>
                  <p className="text-white/80 text-sm">System performance & insights</p>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              <CompactAnalytics />
            </div>
          </motion.div>

          {/* Quick Stats Card */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-gradient-to-br from-indigo-500 to-blue-600 rounded-2xl shadow-lg p-6 text-white"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Quick Stats</h3>
              <TrendingUp className="w-5 h-5" />
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-white/80">Vector Search</span>
                <span className="font-semibold">&lt;100ms</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/80">Memory Reduction</span>
                <span className="font-semibold">75%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/80">Cache Hit Rate</span>
                <span className="font-semibold">95%</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedDashboard;
