import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  FileText, 
  Calendar, 
  Hash, 
  Weight, 
  Tag,
  Clock,
  Database,
  Layers
} from 'lucide-react';
import { Document } from '../services/api';

interface DocumentDetailsModalProps {
  document: Document | null;
  isOpen: boolean;
  onClose: () => void;
}

const DocumentDetailsModal: React.FC<DocumentDetailsModalProps> = ({ 
  document, 
  isOpen, 
  onClose 
}) => {
  if (!document) return null;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
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

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={onClose}
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getFileIcon(document.mime_type)}</span>
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 truncate">
                      {document.title}
                    </h2>
                    <p className="text-sm text-gray-500">{document.filename}</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                {/* Basic Info Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900 flex items-center">
                      <Database className="w-5 h-5 mr-2 text-blue-500" />
                      Document Information
                    </h3>
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="text-sm font-medium text-gray-600 flex items-center">
                          <FileText className="w-4 h-4 mr-2" />
                          File Type
                        </span>
                        <span className="text-sm text-gray-900">{document.mime_type}</span>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="text-sm font-medium text-gray-600 flex items-center">
                          <Weight className="w-4 h-4 mr-2" />
                          File Size
                        </span>
                        <span className="text-sm text-gray-900">{formatFileSize(document.size_bytes)}</span>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="text-sm font-medium text-gray-600 flex items-center">
                          <Hash className="w-4 h-4 mr-2" />
                          Word Count
                        </span>
                        <span className="text-sm text-gray-900">{document.word_count.toLocaleString()}</span>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="text-sm font-medium text-gray-600 flex items-center">
                          <Layers className="w-4 h-4 mr-2" />
                          Chunks
                        </span>
                        <span className="text-sm text-gray-900">{document.chunk_count}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900 flex items-center">
                      <Clock className="w-5 h-5 mr-2 text-green-500" />
                      Processing Details
                    </h3>
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="text-sm font-medium text-gray-600 flex items-center">
                          <Calendar className="w-4 h-4 mr-2" />
                          Uploaded
                        </span>
                        <span className="text-sm text-gray-900">{formatDate(document.uploaded_at)}</span>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="text-sm font-medium text-gray-600">
                          Status
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          ✅ Ready for search
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="text-sm font-medium text-gray-600">
                          Vector Storage
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          🔍 Redis Vector Sets
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tags Section */}
                {document.tags && document.tags.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                      <Tag className="w-5 h-5 mr-2 text-purple-500" />
                      Tags
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {document.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Processing Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Processing Summary</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                    <div className="bg-white rounded-lg p-3">
                      <div className="text-2xl font-bold text-blue-600">{document.chunk_count}</div>
                      <div className="text-sm text-gray-600">Text Chunks</div>
                    </div>
                    <div className="bg-white rounded-lg p-3">
                      <div className="text-2xl font-bold text-green-600">{document.word_count.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Total Words</div>
                    </div>
                    <div className="bg-white rounded-lg p-3">
                      <div className="text-2xl font-bold text-purple-600">{formatFileSize(document.size_bytes)}</div>
                      <div className="text-sm text-gray-600">File Size</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Close
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default DocumentDetailsModal;
