# Specification: File Upload Processing for Schema Agent

**Version:** 1.0
**Date:** December 29, 2025
**Branch:** 012-file-upload-processing
**Status:** Draft

---

## 1. Goal

Enable users to upload files (CSV, Excel, PDF, Images) through ChatKit UI, process them on the backend using Python libraries, and allow Schema Agent to analyze/query the uploaded file content alongside database queries.

---

## 2. Problem Statement

### Current State
- ChatKit has a "+" button for tool selection
- Users can query their connected PostgreSQL database
- No ability to upload and analyze local files
- No support for CSV/Excel data analysis

### User Need
Users want to:
- Upload CSV/Excel files and ask questions about the data
- Upload PDF documents and extract/query information
- Upload images for OCR or visual analysis
- Combine file analysis with database queries

### Solution: Python-Based File Processing
A file upload system that:
- Uses ChatKit's attachment mechanism (+ button)
- Processes files on FastAPI backend using Python libraries
- Creates a temporary "virtual table" from file data
- Allows Schema Agent to query file content
- Supports CSV, Excel, PDF, and Images

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   ChatKit UI                                              │   │
│  │   ├── "+" button → File Upload option                     │   │
│  │   ├── File picker (CSV, Excel, PDF, Image)                │   │
│  │   ├── Upload progress indicator                           │   │
│  │   └── File attachment preview                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ▼ POST /api/files/upload             │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   File Upload Endpoint                                    │   │
│  │   POST /api/files/upload                                  │   │
│  │   ├── Validate file (type, size)                          │   │
│  │   ├── Store temporarily                                   │   │
│  │   └── Return file_id + metadata                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   File Processor Service                                  │   │
│  │   ├── CSV → pandas.read_csv() → DataFrame → JSON          │   │
│  │   ├── Excel → pandas.read_excel() → DataFrame → JSON      │   │
│  │   ├── PDF → pdfplumber → text + tables                    │   │
│  │   └── Image → base64 encode (OCR optional)                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   Schema Agent                                            │   │
│  │   ├── Receives file_id with user message                  │   │
│  │   ├── Loads processed file content                        │   │
│  │   ├── analyze_file tool for file queries                  │   │
│  │   └── Combines with database queries if needed            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Requirements

### 4.1 Supported File Types

| File Type | Extensions | Max Size | Processing Library |
|-----------|------------|----------|-------------------|
| CSV | .csv | 10 MB | pandas |
| Excel | .xlsx, .xls | 10 MB | pandas (openpyxl) |
| PDF | .pdf | 20 MB | pdfplumber |
| Image | .png, .jpg, .jpeg, .gif, .webp | 5 MB | Pillow + base64 |

### 4.2 File Upload Flow

1. User clicks "+" button in ChatKit
2. User selects "Upload File" option
3. File picker opens (filtered by allowed types)
4. User selects file
5. File uploads to backend with progress indicator
6. Backend returns `file_id` and metadata
7. File attachment appears in chat input
8. User types message and sends
9. Schema Agent processes message with file context

### 4.3 File Processing

#### CSV/Excel Processing
```python
# Input: uploaded file
# Output: structured data for agent

{
    "file_id": "abc123",
    "file_name": "sales_data.csv",
    "file_type": "csv",
    "row_count": 1500,
    "column_count": 8,
    "columns": [
        {"name": "date", "type": "datetime", "sample": "2024-01-15"},
        {"name": "product", "type": "string", "sample": "Widget A"},
        {"name": "quantity", "type": "integer", "sample": 150},
        {"name": "price", "type": "float", "sample": 29.99}
    ],
    "preview": [
        {"date": "2024-01-15", "product": "Widget A", "quantity": 150, "price": 29.99},
        {"date": "2024-01-16", "product": "Widget B", "quantity": 200, "price": 19.99}
    ],
    "data_hash": "sha256:...",
    "processed_at": "2025-12-29T10:30:00Z"
}
```

#### PDF Processing
```python
# Input: uploaded PDF
# Output: extracted text and tables

{
    "file_id": "def456",
    "file_name": "report.pdf",
    "file_type": "pdf",
    "page_count": 12,
    "text_content": "Full extracted text...",
    "tables": [
        {
            "page": 3,
            "headers": ["Product", "Q1", "Q2", "Q3", "Q4"],
            "rows": [
                ["Widget A", "100", "150", "200", "180"],
                ["Widget B", "80", "90", "120", "110"]
            ]
        }
    ],
    "has_images": true,
    "processed_at": "2025-12-29T10:30:00Z"
}
```

#### Image Processing
```python
# Input: uploaded image
# Output: base64 + metadata

{
    "file_id": "ghi789",
    "file_name": "chart.png",
    "file_type": "image",
    "width": 1200,
    "height": 800,
    "format": "PNG",
    "base64_content": "data:image/png;base64,...",
    "processed_at": "2025-12-29T10:30:00Z"
}
```

### 4.4 Schema Agent Integration

New agent tool for file analysis:

```python
@function_tool
async def analyze_file(
    file_id: str,
    query: str,
    operation: Literal["summary", "filter", "aggregate", "search", "extract"]
) -> dict:
    """
    Analyze uploaded file content.

    Args:
        file_id: The uploaded file identifier
        query: Natural language query about the file
        operation: Type of analysis to perform
            - summary: Get file overview and statistics
            - filter: Filter data based on conditions
            - aggregate: Calculate sums, averages, counts
            - search: Find specific text/values
            - extract: Extract specific data fields

    Returns:
        Analysis results based on operation type
    """
```

### 4.5 Storage Strategy

```
backend/
└── uploads/
    └── {user_id}/
        └── {file_id}/
            ├── original.{ext}      # Original uploaded file
            ├── processed.json      # Processed data
            └── metadata.json       # File metadata
```

**Cleanup Policy:**
- Files auto-delete after 24 hours
- User can manually delete files
- Max 10 files per user at a time

---

## 5. API Endpoints

### 5.1 File Upload

```
POST /api/files/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

Form Data:
- file: binary (required)
- description: string (optional)

Response 200:
{
    "file_id": "abc123",
    "file_name": "sales_data.csv",
    "file_type": "csv",
    "file_size": 524288,
    "status": "processing",
    "upload_url": null,
    "created_at": "2025-12-29T10:30:00Z"
}

Response 400:
{
    "error": "unsupported_file_type",
    "message": "File type .doc is not supported. Allowed: csv, xlsx, xls, pdf, png, jpg, jpeg, gif, webp"
}

Response 413:
{
    "error": "file_too_large",
    "message": "File size 25MB exceeds maximum 10MB for CSV files"
}
```

### 5.2 Get File Status

```
GET /api/files/{file_id}
Authorization: Bearer {token}

Response 200:
{
    "file_id": "abc123",
    "file_name": "sales_data.csv",
    "file_type": "csv",
    "file_size": 524288,
    "status": "ready",  // processing, ready, error
    "processed_data": {
        "row_count": 1500,
        "column_count": 8,
        "columns": [...],
        "preview": [...]
    },
    "error": null,
    "created_at": "2025-12-29T10:30:00Z",
    "expires_at": "2025-12-30T10:30:00Z"
}
```

### 5.3 Get File Content

```
GET /api/files/{file_id}/content
Authorization: Bearer {token}
Query Params:
- format: json | csv | raw (default: json)
- limit: int (default: 1000, max: 10000)
- offset: int (default: 0)

Response 200 (format=json):
{
    "file_id": "abc123",
    "total_rows": 1500,
    "returned_rows": 1000,
    "offset": 0,
    "data": [
        {"date": "2024-01-15", "product": "Widget A", ...},
        ...
    ]
}
```

### 5.4 Delete File

```
DELETE /api/files/{file_id}
Authorization: Bearer {token}

Response 200:
{
    "status": "deleted",
    "file_id": "abc123"
}
```

### 5.5 List User Files

```
GET /api/files
Authorization: Bearer {token}

Response 200:
{
    "files": [
        {
            "file_id": "abc123",
            "file_name": "sales_data.csv",
            "file_type": "csv",
            "status": "ready",
            "created_at": "2025-12-29T10:30:00Z",
            "expires_at": "2025-12-30T10:30:00Z"
        }
    ],
    "total": 1,
    "max_files": 10
}
```

---

## 6. Database Changes

### 6.1 New Table: uploaded_files

```sql
CREATE TABLE uploaded_files (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(36) UNIQUE NOT NULL,  -- UUID
    user_id INTEGER NOT NULL REFERENCES users(id),
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,  -- csv, xlsx, pdf, image
    file_size INTEGER NOT NULL,  -- bytes
    mime_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'processing',  -- processing, ready, error
    storage_path VARCHAR(500),
    processed_data JSONB,  -- Parsed content
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Auto-delete time
    deleted_at TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('processing', 'ready', 'error', 'deleted'))
);

CREATE INDEX idx_uploaded_files_user ON uploaded_files(user_id);
CREATE INDEX idx_uploaded_files_status ON uploaded_files(status);
CREATE INDEX idx_uploaded_files_expires ON uploaded_files(expires_at) WHERE deleted_at IS NULL;
```

---

## 7. Backend Implementation

### 7.1 New Files

```
backend/app/
├── routers/
│   └── files.py                 # File upload endpoints
├── services/
│   └── file_processor.py        # File processing service
├── models/
│   └── uploaded_file.py         # SQLAlchemy model (or add to models.py)
└── utils/
    └── file_validators.py       # File validation utilities
```

### 7.2 File Processor Service

```python
# backend/app/services/file_processor.py

from typing import Literal
import pandas as pd
import pdfplumber
from PIL import Image
import base64
import io

class FileProcessor:
    """Process uploaded files into structured data."""

    SUPPORTED_TYPES = {
        'csv': {'extensions': ['.csv'], 'max_size': 10 * 1024 * 1024},
        'excel': {'extensions': ['.xlsx', '.xls'], 'max_size': 10 * 1024 * 1024},
        'pdf': {'extensions': ['.pdf'], 'max_size': 20 * 1024 * 1024},
        'image': {'extensions': ['.png', '.jpg', '.jpeg', '.gif', '.webp'], 'max_size': 5 * 1024 * 1024},
    }

    async def process(self, file_path: str, file_type: str) -> dict:
        """Process file and return structured data."""
        if file_type == 'csv':
            return await self._process_csv(file_path)
        elif file_type == 'excel':
            return await self._process_excel(file_path)
        elif file_type == 'pdf':
            return await self._process_pdf(file_path)
        elif file_type == 'image':
            return await self._process_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    async def _process_csv(self, file_path: str) -> dict:
        """Process CSV file using pandas."""
        df = pd.read_csv(file_path)
        return self._dataframe_to_result(df, 'csv')

    async def _process_excel(self, file_path: str) -> dict:
        """Process Excel file using pandas."""
        df = pd.read_excel(file_path)
        return self._dataframe_to_result(df, 'excel')

    async def _process_pdf(self, file_path: str) -> dict:
        """Process PDF using pdfplumber."""
        with pdfplumber.open(file_path) as pdf:
            text_content = ""
            tables = []

            for i, page in enumerate(pdf.pages):
                text_content += page.extract_text() or ""

                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 1:
                        tables.append({
                            "page": i + 1,
                            "headers": table[0],
                            "rows": table[1:]
                        })

            return {
                "page_count": len(pdf.pages),
                "text_content": text_content,
                "tables": tables,
                "has_images": False  # Can be extended
            }

    async def _process_image(self, file_path: str) -> dict:
        """Process image file."""
        with Image.open(file_path) as img:
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format=img.format or 'PNG')
            base64_content = base64.b64encode(buffer.getvalue()).decode()

            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "base64_content": f"data:image/{img.format.lower()};base64,{base64_content}"
            }

    def _dataframe_to_result(self, df: pd.DataFrame, file_type: str) -> dict:
        """Convert pandas DataFrame to result dict."""
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            columns.append({
                "name": str(col),
                "type": self._pandas_dtype_to_type(dtype),
                "sample": str(sample) if sample is not None else None
            })

        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": columns,
            "preview": df.head(10).to_dict(orient='records'),
            "statistics": self._get_statistics(df)
        }

    def _pandas_dtype_to_type(self, dtype: str) -> str:
        """Convert pandas dtype to simple type name."""
        if 'int' in dtype:
            return 'integer'
        elif 'float' in dtype:
            return 'float'
        elif 'datetime' in dtype:
            return 'datetime'
        elif 'bool' in dtype:
            return 'boolean'
        else:
            return 'string'

    def _get_statistics(self, df: pd.DataFrame) -> dict:
        """Get basic statistics for numeric columns."""
        stats = {}
        for col in df.select_dtypes(include=['number']).columns:
            stats[str(col)] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "sum": float(df[col].sum())
            }
        return stats
```

### 7.3 File Router

```python
# backend/app/routers/files.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Annotated
from ..services.file_processor import FileProcessor
from ..models import User, UploadedFile
from ..dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/files", tags=["files"])

@router.post("/upload")
async def upload_file(
    file: Annotated[UploadFile, File(description="File to upload")],
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Upload and process a file."""
    # Validate file type and size
    # Save to storage
    # Process asynchronously
    # Return file_id and metadata
    pass

@router.get("/{file_id}")
async def get_file_status(
    file_id: str,
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get file processing status and metadata."""
    pass

@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    format: str = "json",
    limit: int = 1000,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get processed file content."""
    pass

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete an uploaded file."""
    pass

@router.get("")
async def list_files(
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """List user's uploaded files."""
    pass
```

### 7.4 Schema Agent Tool

```python
# Add to backend/app/agents/schema_query_agent.py

from agents import function_tool

@function_tool
async def analyze_uploaded_file(
    file_id: str,
    query: str,
    operation: str = "summary"
) -> dict:
    """
    Analyze content from an uploaded file.

    Use this tool when the user asks about an uploaded file (CSV, Excel, PDF, or image).

    Args:
        file_id: The file identifier from the upload
        query: What the user wants to know about the file
        operation: Type of analysis:
            - summary: Overview of file contents
            - filter: Filter data by conditions
            - aggregate: Calculate statistics (sum, avg, count)
            - search: Find specific text or values
            - extract: Get specific columns or fields

    Returns:
        Analysis results based on file type and operation
    """
    # Load file from storage
    # Execute analysis based on operation
    # Return formatted results
    pass
```

---

## 8. Frontend Changes

### 8.1 ChatKit Tool Option

Add "Upload File" to ChatKit's tools menu:

```typescript
// Add to tools array in schema-agent/page.tsx

const fileUploadTool: ChatKitToolOption = {
  id: 'file_upload',
  label: 'Upload File',
  shortLabel: 'File',
  icon: 'document',
  placeholderOverride: 'Upload a file to analyze (CSV, Excel, PDF, Image)',
  persistent: false,
};
```

### 8.2 File Upload Handler

```typescript
// frontend/lib/file-upload-api.ts

export interface UploadedFile {
  file_id: string;
  file_name: string;
  file_type: 'csv' | 'excel' | 'pdf' | 'image';
  file_size: number;
  status: 'processing' | 'ready' | 'error';
  processed_data?: any;
  created_at: string;
  expires_at: string;
}

export async function uploadFile(file: File): Promise<UploadedFile> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Upload failed');
  }

  return response.json();
}

export async function getFileStatus(fileId: string): Promise<UploadedFile> {
  const response = await fetch(`${API_BASE_URL}/api/files/${fileId}`, {
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
    },
  });

  return response.json();
}
```

### 8.3 File Attachment Component

```typescript
// frontend/components/chat/FileAttachment.tsx

interface FileAttachmentProps {
  file: UploadedFile;
  onRemove: () => void;
}

export function FileAttachment({ file, onRemove }: FileAttachmentProps) {
  return (
    <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-2">
      <FileIcon type={file.file_type} />
      <div className="flex-1">
        <p className="text-sm font-medium">{file.file_name}</p>
        <p className="text-xs text-gray-500">
          {file.status === 'processing' ? 'Processing...' : 'Ready'}
        </p>
      </div>
      <button onClick={onRemove} className="text-gray-400 hover:text-gray-600">
        <XIcon />
      </button>
    </div>
  );
}
```

---

## 9. Security Requirements

### 9.1 File Validation
- Validate file extension matches content (magic bytes)
- Scan for malicious content patterns
- Sanitize file names
- Reject executable files

### 9.2 Storage Security
- Store files outside web root
- Use random UUIDs for file paths
- Encrypt sensitive files at rest
- Implement proper access control

### 9.3 Processing Security
- Sandbox file processing
- Limit memory usage per file
- Timeout long-running operations
- Log all file operations

---

## 10. Error Handling

| Scenario | Error Code | Message |
|----------|------------|---------|
| Unsupported file type | 400 | "File type .doc is not supported" |
| File too large | 413 | "File size exceeds maximum" |
| Processing failed | 500 | "Failed to process file" |
| File not found | 404 | "File not found or expired" |
| Max files exceeded | 400 | "Maximum 10 files allowed" |
| Processing timeout | 504 | "File processing timed out" |

---

## 11. Dependencies

### New Python Packages

```txt
pandas>=2.0.0
openpyxl>=3.1.0      # Excel support
pdfplumber>=0.10.0   # PDF processing
Pillow>=10.0.0       # Image processing
python-multipart>=0.0.6  # File upload
aiofiles>=23.0.0     # Async file operations
```

---

## 12. Testing Strategy

### Unit Tests
- File type validation
- File size validation
- CSV/Excel parsing
- PDF text extraction
- Image encoding

### Integration Tests
- Full upload flow
- Processing pipeline
- Agent tool integration
- Error scenarios

### Security Tests
- Malicious file upload attempts
- Path traversal attacks
- File type spoofing

---

## 13. Acceptance Criteria

### AC-1: File Upload
- [ ] User can upload CSV files up to 10MB
- [ ] User can upload Excel files up to 10MB
- [ ] User can upload PDF files up to 20MB
- [ ] User can upload images up to 5MB
- [ ] Upload shows progress indicator
- [ ] Invalid files are rejected with clear error

### AC-2: File Processing
- [ ] CSV files are parsed into structured data
- [ ] Excel files are parsed into structured data
- [ ] PDF text and tables are extracted
- [ ] Images are encoded and metadata extracted
- [ ] Processing status is visible to user

### AC-3: Agent Integration
- [ ] Agent can access uploaded file content
- [ ] Agent can answer questions about file data
- [ ] Agent can perform aggregations on tabular data
- [ ] Agent can search text in PDF files
- [ ] File context is included in agent responses

### AC-4: Security
- [ ] Files are validated before processing
- [ ] Files are stored securely
- [ ] Files auto-expire after 24 hours
- [ ] Users can only access their own files

---

## 14. Out of Scope (v1.0)

- Real-time file editing
- File format conversion
- OCR for images (future enhancement)
- Multiple file analysis in single query
- Permanent file storage
- File sharing between users
- Video/audio file support

---

## Appendix A: File Type Icons

| Type | Icon | Color |
|------|------|-------|
| CSV | table | green |
| Excel | file-spreadsheet | green |
| PDF | file-text | red |
| Image | image | blue |

---

## Appendix B: Example User Flows

### Flow 1: CSV Analysis
```
1. User: Clicks "+" → "Upload File"
2. User: Selects "sales_q4.csv"
3. System: Shows upload progress
4. System: Shows "File ready" attachment
5. User: "What are the top 5 products by revenue?"
6. Agent: Analyzes CSV, returns:
   "Based on sales_q4.csv, the top 5 products by revenue are:
   1. Widget Pro - $45,230
   2. Super Gadget - $38,120
   ..."
```

### Flow 2: PDF Search
```
1. User: Uploads "annual_report.pdf"
2. User: "Find all mentions of revenue growth"
3. Agent: Searches PDF text, returns:
   "I found 3 mentions of revenue growth in annual_report.pdf:
   - Page 4: '...revenue growth of 23% compared to...'
   - Page 12: '...projected revenue growth for 2025...'
   ..."
```

### Flow 3: Combined Query
```
1. User: Has database connected + uploads "budget.xlsx"
2. User: "Compare my actual sales from database with budget in the Excel file"
3. Agent: Queries database AND Excel, returns:
   "Comparing actual sales (database) vs budget (budget.xlsx):
   - Q1: Actual $120k vs Budget $100k (+20%)
   - Q2: Actual $95k vs Budget $110k (-14%)
   ..."
```
