/**
 * File Upload API for Schema Agent
 *
 * Handles file upload, status checking, and deletion for the Schema Agent.
 * Uploaded files can be analyzed by the AI agent.
 */

import { API_BASE_URL } from './constants';
import { getAccessToken } from './auth-api';

// ============================================================================
// Types
// ============================================================================

export interface UploadedFile {
  file_id: string;
  file_name: string;
  file_type: 'csv' | 'excel' | 'pdf' | 'image';
  file_size: number;
  status: 'processing' | 'ready' | 'error' | 'deleted';
  processed_data?: ProcessedFileData;
  error_message?: string;
  created_at: string;
  expires_at?: string;
}

export interface ProcessedFileData {
  // CSV/Excel
  row_count?: number;
  column_count?: number;
  columns?: ColumnInfo[];
  preview?: Record<string, any>[];
  statistics?: Record<string, ColumnStats>;

  // PDF
  page_count?: number;
  text_content?: string;
  tables?: TableData[];

  // Image
  width?: number;
  height?: number;
  format?: string;
  base64_content?: string;
}

export interface ColumnInfo {
  name: string;
  type: string;
  dtype?: string;
  sample?: string;
  null_count?: number;
  unique_count?: number;
}

export interface ColumnStats {
  min?: number;
  max?: number;
  mean?: number;
  sum?: number;
  std?: number;
}

export interface TableData {
  page: number;
  headers: string[];
  rows: string[][];
}

export interface FileListResponse {
  files: UploadedFile[];
  total: number;
  max_files: number;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// ============================================================================
// Constants
// ============================================================================

export const SUPPORTED_FILE_TYPES = {
  csv: {
    extensions: ['.csv'],
    maxSize: 10 * 1024 * 1024, // 10 MB
    mimeTypes: ['text/csv', 'application/csv'],
    label: 'CSV',
  },
  excel: {
    extensions: ['.xlsx', '.xls'],
    maxSize: 10 * 1024 * 1024, // 10 MB
    mimeTypes: [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ],
    label: 'Excel',
  },
  pdf: {
    extensions: ['.pdf'],
    maxSize: 20 * 1024 * 1024, // 20 MB
    mimeTypes: ['application/pdf'],
    label: 'PDF',
  },
  image: {
    extensions: ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
    maxSize: 5 * 1024 * 1024, // 5 MB
    mimeTypes: ['image/png', 'image/jpeg', 'image/gif', 'image/webp'],
    label: 'Image',
  },
};

export const ALLOWED_EXTENSIONS = Object.values(SUPPORTED_FILE_TYPES)
  .flatMap((t) => t.extensions)
  .join(',');

export const MAX_FILES_PER_USER = 10;

// ============================================================================
// Helper Functions
// ============================================================================

function getHeaders(): HeadersInit {
  const token = getAccessToken();
  return {
    Authorization: `Bearer ${token}`,
  };
}

function getJsonHeaders(): HeadersInit {
  const token = getAccessToken();
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

export function getFileType(filename: string): string | null {
  const ext = filename.toLowerCase().slice(filename.lastIndexOf('.'));
  for (const [type, config] of Object.entries(SUPPORTED_FILE_TYPES)) {
    if (config.extensions.includes(ext)) {
      return type;
    }
  }
  return null;
}

export function validateFile(file: File): { valid: boolean; error?: string } {
  const fileType = getFileType(file.name);

  if (!fileType) {
    return {
      valid: false,
      error: `Unsupported file type. Allowed: ${ALLOWED_EXTENSIONS}`,
    };
  }

  const config = SUPPORTED_FILE_TYPES[fileType as keyof typeof SUPPORTED_FILE_TYPES];
  if (file.size > config.maxSize) {
    const maxMB = config.maxSize / (1024 * 1024);
    const actualMB = (file.size / (1024 * 1024)).toFixed(1);
    return {
      valid: false,
      error: `File size (${actualMB}MB) exceeds maximum (${maxMB}MB) for ${config.label} files`,
    };
  }

  return { valid: true };
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Upload a file for analysis
 */
export async function uploadFile(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<UploadedFile> {
  // Validate file first
  const validation = validateFile(file);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  const formData = new FormData();
  formData.append('file', file);

  // Use XMLHttpRequest for progress tracking
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/files/upload`);

    // Add auth header
    const token = getAccessToken();
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);

    // Track upload progress
    if (onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress({
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded / event.total) * 100),
          });
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (e) {
          reject(new Error('Invalid response from server'));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail?.message || error.message || 'Upload failed'));
        } catch {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => {
      reject(new Error('Network error during upload'));
    };

    xhr.send(formData);
  });
}

/**
 * Get file status and metadata
 */
export async function getFileStatus(fileId: string): Promise<UploadedFile> {
  const response = await fetch(`${API_BASE_URL}/api/files/${fileId}`, {
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || 'Failed to get file status');
  }

  return response.json();
}

/**
 * Get file content (for preview)
 */
export async function getFileContent(
  fileId: string,
  options?: { format?: 'json' | 'csv' | 'raw'; limit?: number; offset?: number }
): Promise<any> {
  const params = new URLSearchParams();
  if (options?.format) params.set('format', options.format);
  if (options?.limit) params.set('limit', options.limit.toString());
  if (options?.offset) params.set('offset', options.offset.toString());

  const url = `${API_BASE_URL}/api/files/${fileId}/content?${params.toString()}`;
  const response = await fetch(url, {
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || 'Failed to get file content');
  }

  return response.json();
}

/**
 * Delete an uploaded file
 */
export async function deleteFile(fileId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/files/${fileId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || 'Failed to delete file');
  }
}

/**
 * List all uploaded files
 */
export async function listFiles(): Promise<FileListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/files`, {
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || 'Failed to list files');
  }

  return response.json();
}

/**
 * Wait for file to be processed
 */
export async function waitForFileReady(
  fileId: string,
  maxWaitMs: number = 30000,
  pollIntervalMs: number = 1000
): Promise<UploadedFile> {
  const startTime = Date.now();

  while (Date.now() - startTime < maxWaitMs) {
    const file = await getFileStatus(fileId);

    if (file.status === 'ready') {
      return file;
    }

    if (file.status === 'error') {
      throw new Error(file.error_message || 'File processing failed');
    }

    // Wait before next poll
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
  }

  throw new Error('File processing timed out');
}
