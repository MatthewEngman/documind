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
    // Filter out files that are already being uploaded
    const filteredFiles = acceptedFiles.filter(file => {
      const isDuplicate = uploads.some(upload => 
        upload.file.name === file.name && 
        upload.file.size === file.size &&
        (upload.status === 'uploading' || upload.status === 'processing')
      );
      if (isDuplicate) {
        toast.error(`${file.name} is already being uploaded`);
      }
      return !isDuplicate;
    });

    if (filteredFiles.length === 0) return;

    // Initialize upload progress
    const newUploads: UploadProgress[] = filteredFiles.map(file => ({
      file,
      status: 'uploading',
      progress: 0,
    }));

    setUploads(prev => [...prev, ...newUploads]);

    const MAX_CONCURRENT_UPLOADS = 3;
    
    const processFilesConcurrently = async () => {
      const uploadPromises = filteredFiles.map(async (file, index) => {
        const uploadIndex = uploads.length + index;
        
        try {
          // Update progress to processing
          setUploads(prev => prev.map((upload, idx) => 
            idx === uploadIndex 
              ? { ...upload, status: 'processing', progress: 50 }
              : upload
          ));

          // Upload file with progress tracking
          const result = await documentApi.upload(file, (uploadProgress) => {
            // Update upload progress in real-time
            setUploads(prev => prev.map((upload, idx) => 
              idx === uploadIndex 
                ? { ...upload, progress: Math.min(uploadProgress, 45) } // Cap at 45% for upload phase
                : upload
            ));
          });
          
          const docId = result.doc_id;
          let completed = false;
          let attempts = 0;
          
          // Dynamic timeout based on file size (minimum 2 minutes, +1 minute per MB)
          const fileSizeMB = file.size / (1024 * 1024);
          const maxAttempts = Math.max(120, 120 + (fileSizeMB * 60)); // 2min base + 1min per MB
          
          // Dynamic polling frequency - faster for smaller files, slower for larger ones
          const pollInterval = fileSizeMB > 5 ? 2000 : 1000; // 2s for large files, 1s for small
          
          while (!completed && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, pollInterval));
            
            try {
              const statusResult = await documentApi.getStatus(docId);
              
              // Update progress with better mapping
              const mappedProgress = statusResult.progress || (45 + (attempts / maxAttempts) * 50); // Start from 45% (after upload)
              setUploads(prev => prev.map((upload, idx) => 
                idx === uploadIndex 
                  ? { 
                      ...upload, 
                      status: statusResult.status === 'completed' ? 'success' : 'processing',
                      progress: Math.min(mappedProgress, 99) // Cap at 99% until completed
                    }
                  : upload
              ));
              
              if (statusResult.status === 'completed') {
                completed = true;
                // Update to success
                setUploads(prev => prev.map((upload, idx) => 
                  idx === uploadIndex 
                    ? { 
                        ...upload, 
                        status: 'success', 
                        progress: 100,
                        docId: docId 
                      }
                    : upload
                ));
                
                toast.success(`${file.name} uploaded successfully!`);
                
                // Add a small delay to ensure document is available in API before refreshing list
                setTimeout(() => {
                  onUploadSuccess();
                }, 500);
                
                return { success: true, file: file.name };
              } else if (statusResult.status === 'failed') {
                throw new Error(statusResult.message || 'Processing failed');
              }
            } catch (statusError) {
              // Warn user if processing is taking longer than expected for large files
              if (fileSizeMB > 5 && attempts === Math.floor(maxAttempts * 0.5)) {
                toast(`Large file (${fileSizeMB.toFixed(1)}MB) is still processing... This may take a few more minutes.`, {
                  icon: '⏳',
                  duration: 5000
                });
              }
              
              if (attempts === maxAttempts - 1) {
                throw new Error(`Processing timeout after ${Math.round(maxAttempts * pollInterval / 1000 / 60)} minutes. Large files may need more time - please try again.`);
              }
            }
            
            attempts++;
          }

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
          return { success: false, file: file.name, error: error.message };
        }
      });

      // Process uploads with controlled concurrency
      const results = [];
      for (let i = 0; i < uploadPromises.length; i += MAX_CONCURRENT_UPLOADS) {
        const batch = uploadPromises.slice(i, i + MAX_CONCURRENT_UPLOADS);
        const batchResults = await Promise.all(batch);
        results.push(...batchResults);
      }
      
      return results;
    };

    await processFilesConcurrently();
  }, [onUploadSuccess]); // Remove uploads.length dependency to prevent recreation

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
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
          ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'}
        `}
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
      </div>

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
