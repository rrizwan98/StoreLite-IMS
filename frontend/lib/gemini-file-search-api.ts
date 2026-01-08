/**
 * Gemini File Search API Client
 *
 * Handles file upload to Gemini File Search store, status checking,
 * and deletion. Files are stored permanently with embeddings for
 * semantic search via the schema_agent.
 *
 * Version: 1.0
 * Date: December 30, 2025
 */

import { API_BASE_URL } from './constants';
import { getAccessToken } from './auth-api';

// ============================================================================
// Types
// ============================================================================

export interface GeminiFileDocument {
  id: number;
  filename: string;
  status: 'processing' | 'ready' | 'failed';
  size: number;
  mime_type: string;
  created_at: string;
  error?: string | null;
}

export interface GeminiUploadResponse {
  id: number;
  filename: string;
  status: string;
  message: string;
}

export interface GeminiFileListResponse {
  files: GeminiFileDocument[];
  total: number;
}

export interface GeminiFileStatusResponse {
  id: number;
  filename: string;
  status: string;
  error?: string | null;
}

export interface GeminiSearchResponse {
  has_files: boolean;
  processing: boolean;
  answer: string;
  citations: GeminiCitation[];
  error?: string;
}

export interface GeminiCitation {
  source: string;
  text: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// ============================================================================
// Constants
// ============================================================================

export const GEMINI_SUPPORTED_FILE_TYPES = {
  pdf: {
    extensions: ['.pdf'],
    maxSize: 50 * 1024 * 1024, // 50 MB
    mimeTypes: ['application/pdf'],
    label: 'PDF',
  },
  excel: {
    extensions: ['.xlsx', '.xls'],
    maxSize: 20 * 1024 * 1024, // 20 MB
    mimeTypes: [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ],
    label: 'Excel',
  },
  csv: {
    extensions: ['.csv'],
    maxSize: 20 * 1024 * 1024, // 20 MB
    mimeTypes: ['text/csv', 'application/csv', 'text/plain'],
    label: 'CSV',
  },
  word: {
    extensions: ['.docx', '.doc'],
    maxSize: 20 * 1024 * 1024, // 20 MB
    mimeTypes: [
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
    ],
    label: 'Word',
  },
  text: {
    extensions: ['.txt', '.md'],
    maxSize: 10 * 1024 * 1024, // 10 MB
    mimeTypes: ['text/plain', 'text/markdown'],
    label: 'Text',
  },
  image: {
    extensions: ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
    maxSize: 10 * 1024 * 1024, // 10 MB
    mimeTypes: ['image/png', 'image/jpeg', 'image/gif', 'image/webp'],
    label: 'Image',
  },
};

export const GEMINI_ALLOWED_EXTENSIONS = Object.values(GEMINI_SUPPORTED_FILE_TYPES)
  .flatMap((t) => t.extensions)
  .join(',');

export const GEMINI_MAX_FILES_PER_USER = 20;

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

export function getGeminiFileType(filename: string): string | null {
  const ext = filename.toLowerCase().slice(filename.lastIndexOf('.'));
  for (const [type, config] of Object.entries(GEMINI_SUPPORTED_FILE_TYPES)) {
    if (config.extensions.includes(ext)) {
      return type;
    }
  }
  return null;
}

export function validateGeminiFile(file: File): { valid: boolean; error?: string } {
  const fileType = getGeminiFileType(file.name);

  if (!fileType) {
    return {
      valid: false,
      error: `Unsupported file type. Allowed: ${GEMINI_ALLOWED_EXTENSIONS}`,
    };
  }

  const config = GEMINI_SUPPORTED_FILE_TYPES[fileType as keyof typeof GEMINI_SUPPORTED_FILE_TYPES];
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
 * Upload a file to Gemini File Search store
 */
export async function uploadGeminiFile(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<GeminiUploadResponse> {
  // Validate file first
  const validation = validateGeminiFile(file);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  const formData = new FormData();
  formData.append('file', file);

  // Use XMLHttpRequest for progress tracking
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/file-search/upload`);

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
          reject(new Error(error.detail?.message || error.detail || error.message || 'Upload failed'));
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
 * List all files in user's Gemini File Search store
 */
export async function listGeminiFiles(): Promise<GeminiFileListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/file-search/files`, {
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || error.detail || 'Failed to list files');
  }

  return response.json();
}

/**
 * Get status of a specific file
 */
export async function getGeminiFileStatus(documentId: number): Promise<GeminiFileStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/file-search/files/${documentId}/status`, {
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || error.detail || 'Failed to get file status');
  }

  return response.json();
}

/**
 * Delete a file from Gemini File Search store
 */
export async function deleteGeminiFile(documentId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/file-search/files/${documentId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || error.detail || 'Failed to delete file');
  }
}

/**
 * Search files using natural language query
 * (Usually done via schema_agent's file_search tool, but can be called directly)
 */
export async function searchGeminiFiles(query: string): Promise<GeminiSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/file-search/search`, {
    method: 'POST',
    headers: getJsonHeaders(),
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail?.message || error.detail || 'Search failed');
  }

  return response.json();
}

/**
 * Wait for a file to finish processing
 */
export async function waitForGeminiFileReady(
  documentId: number,
  maxWaitMs: number = 60000,
  pollIntervalMs: number = 2000
): Promise<GeminiFileDocument> {
  const startTime = Date.now();

  while (Date.now() - startTime < maxWaitMs) {
    const statusResponse = await getGeminiFileStatus(documentId);

    if (statusResponse.status === 'ready') {
      // Convert status response to document format
      return {
        id: statusResponse.id,
        filename: statusResponse.filename,
        status: 'ready' as const,
        size: 0,
        mime_type: '',
        created_at: new Date().toISOString(),
        error: statusResponse.error || null,
      };
    }

    if (statusResponse.status === 'failed') {
      throw new Error(statusResponse.error || 'File processing failed');
    }

    // Wait before next poll
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
  }

  throw new Error('File processing timed out');
}
