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
    <div className="space-y-4 max-h-[600px] overflow-hidden flex flex-col">
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

      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
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
                                toast('Download feature coming soon!', { icon: '📥' });
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
