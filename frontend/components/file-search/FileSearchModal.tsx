/**
 * FileSearchModal Component
 *
 * Modal for managing Gemini File Search files - uploading new files,
 * viewing existing files, checking status, and deleting files.
 *
 * Files are stored permanently in Gemini's File Search store with
 * embeddings for semantic search via the schema_agent.
 *
 * Version: 1.0
 * Date: December 30, 2025
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Upload, File, Trash2, RefreshCw, CheckCircle, AlertCircle, Clock, Search } from 'lucide-react';
import {
  GeminiFileDocument,
  uploadGeminiFile,
  listGeminiFiles,
  deleteGeminiFile,
  validateGeminiFile,
  formatFileSize,
  GEMINI_ALLOWED_EXTENSIONS,
  GEMINI_MAX_FILES_PER_USER,
  UploadProgress,
} from '@/lib/gemini-file-search-api';

interface FileSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFilesReady?: () => void; // Callback when files are ready for searching
}

type ModalView = 'list' | 'upload';

// File type icon mapping
const FILE_ICONS: Record<string, string> = {
  'application/pdf': 'PDF',
  'text/csv': 'CSV',
  'application/csv': 'CSV',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
  'application/vnd.ms-excel': 'XLS',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
  'application/msword': 'DOC',
  'text/plain': 'TXT',
  'text/markdown': 'MD',
  'image/png': 'PNG',
  'image/jpeg': 'JPG',
  'image/gif': 'GIF',
  'image/webp': 'WEBP',
};

function getFileIcon(mimeType: string): string {
  return FILE_ICONS[mimeType] || 'FILE';
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'ready':
      return 'text-green-600 bg-green-50';
    case 'processing':
      return 'text-amber-600 bg-amber-50';
    case 'failed':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'ready':
      return <CheckCircle className="h-4 w-4" />;
    case 'processing':
      return <Clock className="h-4 w-4 animate-pulse" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4" />;
    default:
      return null;
  }
}

export default function FileSearchModal({
  isOpen,
  onClose,
  onFilesReady,
}: FileSearchModalProps) {
  const [view, setView] = useState<ModalView>('list');
  const [files, setFiles] = useState<GeminiFileDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [readyCount, setReadyCount] = useState(0);
  const [processingCount, setProcessingCount] = useState(0);

  // Upload state
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, UploadProgress>>({});
  const [uploadErrors, setUploadErrors] = useState<Record<string, string>>({});
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Polling for processing files
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Load files when modal opens
  useEffect(() => {
    if (isOpen) {
      loadFiles();
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [isOpen]);

  // Start polling when there are processing files
  useEffect(() => {
    if (processingCount > 0 && !pollingRef.current) {
      pollingRef.current = setInterval(() => {
        loadFiles();
      }, 3000); // Poll every 3 seconds
    } else if (processingCount === 0 && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      // Notify parent that files are ready
      if (readyCount > 0 && onFilesReady) {
        onFilesReady();
      }
    }
  }, [processingCount, readyCount, onFilesReady]);

  const loadFiles = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await listGeminiFiles();
      setFiles(response.files);
      // Calculate ready/processing counts from files
      const ready = response.files.filter(f => f.status === 'ready').length;
      const processing = response.files.filter(f => f.status === 'processing').length;
      setReadyCount(ready);
      setProcessingCount(processing);
    } catch (err) {
      console.error('[FileSearchModal] Failed to load files:', err);
      setError(err instanceof Error ? err.message : 'Failed to load files');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList) return;

    const newFiles: File[] = [];
    const newErrors: Record<string, string> = {};

    Array.from(fileList).forEach((file) => {
      const validation = validateGeminiFile(file);
      if (validation.valid) {
        newFiles.push(file);
      } else {
        newErrors[file.name] = validation.error || 'Invalid file';
      }
    });

    setSelectedFiles((prev) => [...prev, ...newFiles]);
    setUploadErrors((prev) => ({ ...prev, ...newErrors }));

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveSelectedFile = (fileName: string) => {
    setSelectedFiles((prev) => prev.filter((f) => f.name !== fileName));
    setUploadErrors((prev) => {
      const next = { ...prev };
      delete next[fileName];
      return next;
    });
    setUploadProgress((prev) => {
      const next = { ...prev };
      delete next[fileName];
      return next;
    });
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadErrors({});

    const uploadPromises = selectedFiles.map(async (file) => {
      try {
        await uploadGeminiFile(file, (progress) => {
          setUploadProgress((prev) => ({
            ...prev,
            [file.name]: progress,
          }));
        });
        return { success: true, fileName: file.name };
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Upload failed';
        setUploadErrors((prev) => ({
          ...prev,
          [file.name]: errorMessage,
        }));
        return { success: false, fileName: file.name, error: errorMessage };
      }
    });

    await Promise.all(uploadPromises);

    // Clear successfully uploaded files
    const failedFiles = Object.keys(uploadErrors);
    setSelectedFiles((prev) => prev.filter((f) => failedFiles.includes(f.name)));
    setUploadProgress({});
    setIsUploading(false);

    // Refresh file list
    await loadFiles();

    // Go back to list view if all uploads succeeded
    if (failedFiles.length === 0) {
      setView('list');
      setSelectedFiles([]);
    }
  };

  const handleDeleteFile = async (documentId: number, filename: string) => {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;

    try {
      await deleteGeminiFile(documentId);
      const deletedFile = files.find((f) => f.id === documentId);
      setFiles((prev) => prev.filter((f) => f.id !== documentId));
      // Update counts
      if (deletedFile?.status === 'ready') {
        setReadyCount((prev) => prev - 1);
      } else if (deletedFile?.status === 'processing') {
        setProcessingCount((prev) => prev - 1);
      }
    } catch (err) {
      console.error('[FileSearchModal] Failed to delete file:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete file');
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-full md:max-w-2xl md:max-h-[80vh] bg-white rounded-xl shadow-xl z-50 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Search className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {view === 'list' ? 'File Search' : 'Upload Files'}
              </h2>
              <p className="text-sm text-gray-500">
                {view === 'list'
                  ? 'Manage files for semantic search'
                  : 'Add files to your search library'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {/* Error Banner */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
              <div className="flex items-center space-x-2 text-red-700">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">{error}</span>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-500 hover:text-red-700"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {view === 'list' && (
            <>
              {/* Stats Bar */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-500">
                    {files.length} / {GEMINI_MAX_FILES_PER_USER} files
                  </span>
                  {readyCount > 0 && (
                    <span className="text-sm text-green-600 bg-green-50 px-2 py-1 rounded-full">
                      {readyCount} ready
                    </span>
                  )}
                  {processingCount > 0 && (
                    <span className="text-sm text-amber-600 bg-amber-50 px-2 py-1 rounded-full flex items-center space-x-1">
                      <RefreshCw className="h-3 w-3 animate-spin" />
                      <span>{processingCount} processing</span>
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={loadFiles}
                    disabled={isLoading}
                    className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                    title="Refresh"
                  >
                    <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                  </button>
                  <button
                    onClick={() => setView('upload')}
                    disabled={files.length >= GEMINI_MAX_FILES_PER_USER}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    <Upload className="h-4 w-4" />
                    <span>Upload Files</span>
                  </button>
                </div>
              </div>

              {/* File List */}
              {isLoading && files.length === 0 ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : files.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <File className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No files yet</h3>
                  <p className="text-gray-500 mb-4">
                    Upload PDF, Excel, Word, or text files to enable semantic search.
                  </p>
                  <button
                    onClick={() => setView('upload')}
                    className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Upload className="h-4 w-4" />
                    <span>Upload Your First File</span>
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  {files.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <div className="flex-shrink-0 w-10 h-10 bg-white border rounded-lg flex items-center justify-center">
                          <span className="text-xs font-medium text-gray-500">
                            {getFileIcon(file.mime_type)}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate" title={file.filename}>
                            {file.filename}
                          </p>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-xs text-gray-500">
                              {formatFileSize(file.size)}
                            </span>
                            <span className="text-gray-300">|</span>
                            <span className={`inline-flex items-center space-x-1 text-xs px-2 py-0.5 rounded-full ${getStatusColor(file.status)}`}>
                              {getStatusIcon(file.status)}
                              <span className="capitalize">{file.status}</span>
                            </span>
                          </div>
                          {file.status === 'failed' && file.error && (
                            <p className="text-xs text-red-600 mt-1">{file.error}</p>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteFile(file.id, file.filename)}
                        className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete file"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Info Banner */}
              {files.length > 0 && readyCount > 0 && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <strong>Tip:</strong> Ask questions about your files in the chat! The AI will search through your documents and provide answers with citations.
                  </p>
                </div>
              )}
            </>
          )}

          {view === 'upload' && (
            <>
              {/* Upload Drop Zone */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 hover:bg-blue-50 cursor-pointer transition-colors"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept={GEMINI_ALLOWED_EXTENSIONS}
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">
                  Click to select files
                </p>
                <p className="text-sm text-gray-500">
                  PDF, Excel, Word, CSV, TXT, MD, Images
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  Max 50MB per PDF, 20MB for other documents
                </p>
              </div>

              {/* Selected Files */}
              {(selectedFiles.length > 0 || Object.keys(uploadErrors).length > 0) && (
                <div className="mt-4 space-y-2">
                  <h3 className="text-sm font-medium text-gray-700">
                    Selected Files ({selectedFiles.length})
                  </h3>
                  {selectedFiles.map((file) => {
                    const progress = uploadProgress[file.name];
                    const error = uploadErrors[file.name];
                    return (
                      <div
                        key={file.name}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                          <File className="h-5 w-5 text-gray-400 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-900 truncate">{file.name}</p>
                            <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                            {progress && (
                              <div className="mt-1">
                                <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-blue-600 transition-all"
                                    style={{ width: `${progress.percentage}%` }}
                                  />
                                </div>
                              </div>
                            )}
                            {error && (
                              <p className="text-xs text-red-600 mt-1">{error}</p>
                            )}
                          </div>
                        </div>
                        {!isUploading && (
                          <button
                            onClick={() => handleRemoveSelectedFile(file.name)}
                            className="p-1 text-gray-400 hover:text-red-600"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
                <button
                  onClick={() => {
                    setView('list');
                    setSelectedFiles([]);
                    setUploadErrors({});
                    setUploadProgress({});
                  }}
                  disabled={isUploading}
                  className="px-4 py-2 text-gray-700 hover:text-gray-900 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={selectedFiles.length === 0 || isUploading}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      <span>Upload {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}</span>
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 border-t">
          <p className="text-xs text-gray-500 text-center">
            Files are stored securely with embeddings for semantic search. Ask questions in the chat to search your files.
          </p>
        </div>
      </div>
    </>
  );
}
