"""
File Processing Service for handling uploaded files.

Supports:
- CSV files (via pandas)
- Excel files (via pandas + openpyxl)
- PDF files (via pdfplumber)
- Image files (via Pillow)

Version: 1.0
Date: December 29, 2025
"""

import io
import base64
import hashlib
import logging
from pathlib import Path
from typing import Literal, Optional, Any
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


class FileProcessor:
    """Process uploaded files into structured data for Schema Agent."""

    SUPPORTED_TYPES = {
        'csv': {
            'extensions': ['.csv'],
            'max_size': 10 * 1024 * 1024,  # 10 MB
            'mime_types': ['text/csv', 'application/csv']
        },
        'excel': {
            'extensions': ['.xlsx', '.xls'],
            'max_size': 10 * 1024 * 1024,  # 10 MB
            'mime_types': [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ]
        },
        'pdf': {
            'extensions': ['.pdf'],
            'max_size': 20 * 1024 * 1024,  # 20 MB
            'mime_types': ['application/pdf']
        },
        'image': {
            'extensions': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
            'max_size': 5 * 1024 * 1024,  # 5 MB
            'mime_types': ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
        },
    }

    @classmethod
    def get_file_type(cls, filename: str, mime_type: Optional[str] = None) -> Optional[str]:
        """Determine file type from filename extension or MIME type."""
        ext = Path(filename).suffix.lower()

        for file_type, config in cls.SUPPORTED_TYPES.items():
            if ext in config['extensions']:
                return file_type
            if mime_type and mime_type in config['mime_types']:
                return file_type

        return None

    @classmethod
    def validate_file(cls, filename: str, file_size: int, mime_type: Optional[str] = None) -> tuple[bool, str, Optional[str]]:
        """
        Validate file type and size.

        Returns:
            Tuple of (is_valid, error_message, file_type)
        """
        file_type = cls.get_file_type(filename, mime_type)

        if not file_type:
            ext = Path(filename).suffix.lower()
            allowed = ', '.join([
                ext for config in cls.SUPPORTED_TYPES.values()
                for ext in config['extensions']
            ])
            return False, f"Unsupported file type '{ext}'. Allowed: {allowed}", None

        max_size = cls.SUPPORTED_TYPES[file_type]['max_size']
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"File size ({actual_mb:.1f}MB) exceeds maximum ({max_mb:.0f}MB) for {file_type} files", None

        return True, "", file_type

    async def process(self, file_path: str, file_type: str, file_name: str) -> dict:
        """
        Process file and return structured data.

        Args:
            file_path: Path to the uploaded file
            file_type: Type of file (csv, excel, pdf, image)
            file_name: Original filename

        Returns:
            Dictionary with processed file data
        """
        try:
            if file_type == 'csv':
                result = await self._process_csv(file_path)
            elif file_type == 'excel':
                result = await self._process_excel(file_path)
            elif file_type == 'pdf':
                result = await self._process_pdf(file_path)
            elif file_type == 'image':
                result = await self._process_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Add common metadata
            result['file_name'] = file_name
            result['file_type'] = file_type
            result['processed_at'] = datetime.utcnow().isoformat() + 'Z'

            # Calculate data hash for caching/dedup
            result['data_hash'] = self._calculate_hash(file_path)

            return result

        except Exception as e:
            logger.error(f"Error processing file {file_name}: {e}")
            raise

    async def _process_csv(self, file_path: str) -> dict:
        """Process CSV file using pandas."""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode CSV file with supported encodings")

            return self._dataframe_to_result(df)

        except pd.errors.EmptyDataError:
            return {
                'row_count': 0,
                'column_count': 0,
                'columns': [],
                'preview': [],
                'statistics': {},
                'is_empty': True
            }

    async def _process_excel(self, file_path: str) -> dict:
        """Process Excel file using pandas."""
        try:
            # Read first sheet by default
            df = pd.read_excel(file_path, sheet_name=0)

            # Get all sheet names for metadata
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names

            result = self._dataframe_to_result(df)
            result['sheet_names'] = sheet_names
            result['active_sheet'] = sheet_names[0] if sheet_names else None

            return result

        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            raise ValueError(f"Failed to process Excel file: {str(e)}")

    async def _process_pdf(self, file_path: str) -> dict:
        """Process PDF using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed, returning basic PDF info")
            return {
                'page_count': 0,
                'text_content': '',
                'tables': [],
                'has_images': False,
                'error': 'PDF processing not available (pdfplumber not installed)'
            }

        try:
            with pdfplumber.open(file_path) as pdf:
                text_content = ""
                tables = []
                page_count = len(pdf.pages)

                # Process each page (limit to first 50 pages for performance)
                for i, page in enumerate(pdf.pages[:50]):
                    # Extract text
                    page_text = page.extract_text() or ""
                    text_content += f"\n--- Page {i + 1} ---\n{page_text}"

                    # Extract tables
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table and len(table) > 1:
                            # First row as headers, rest as data
                            headers = [str(h) if h else f"Column_{j}" for j, h in enumerate(table[0])]
                            rows = [
                                [str(cell) if cell else "" for cell in row]
                                for row in table[1:]
                            ]
                            tables.append({
                                "page": i + 1,
                                "headers": headers,
                                "rows": rows[:100]  # Limit rows per table
                            })

                return {
                    'page_count': page_count,
                    'text_content': text_content.strip()[:50000],  # Limit text size
                    'text_length': len(text_content),
                    'tables': tables[:20],  # Limit number of tables
                    'table_count': len(tables),
                    'has_images': False  # Could be extended with image extraction
                }

        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise ValueError(f"Failed to process PDF: {str(e)}")

    async def _process_image(self, file_path: str) -> dict:
        """Process image file using Pillow."""
        try:
            from PIL import Image
        except ImportError:
            logger.warning("Pillow not installed, returning basic image info")
            return {
                'width': 0,
                'height': 0,
                'format': 'unknown',
                'base64_content': None,
                'error': 'Image processing not available (Pillow not installed)'
            }

        try:
            with Image.open(file_path) as img:
                # Get basic info
                width, height = img.size
                img_format = img.format or 'PNG'
                mode = img.mode

                # Convert to base64 for embedding
                buffer = io.BytesIO()

                # Convert RGBA to RGB for JPEG
                if img_format.upper() == 'JPEG' and mode == 'RGBA':
                    img = img.convert('RGB')

                img.save(buffer, format=img_format)
                base64_content = base64.b64encode(buffer.getvalue()).decode()

                return {
                    'width': width,
                    'height': height,
                    'format': img_format,
                    'mode': mode,
                    'base64_content': f"data:image/{img_format.lower()};base64,{base64_content}"
                }

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise ValueError(f"Failed to process image: {str(e)}")

    def _dataframe_to_result(self, df: pd.DataFrame) -> dict:
        """Convert pandas DataFrame to result dictionary."""
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null = df[col].dropna()
            sample = str(non_null.iloc[0]) if len(non_null) > 0 else None

            columns.append({
                "name": str(col),
                "type": self._pandas_dtype_to_type(dtype),
                "dtype": dtype,
                "sample": sample,
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique())
            })

        # Get preview rows (first 20)
        preview = df.head(20).fillna('').to_dict(orient='records')

        # Convert any non-serializable types in preview
        for row in preview:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                elif hasattr(value, 'isoformat'):  # datetime
                    row[key] = value.isoformat()
                else:
                    row[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value

        return {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': columns,
            'preview': preview,
            'statistics': self._get_statistics(df),
            'is_empty': len(df) == 0
        }

    def _pandas_dtype_to_type(self, dtype: str) -> str:
        """Convert pandas dtype to simple type name."""
        dtype_lower = dtype.lower()
        if 'int' in dtype_lower:
            return 'integer'
        elif 'float' in dtype_lower:
            return 'float'
        elif 'datetime' in dtype_lower:
            return 'datetime'
        elif 'bool' in dtype_lower:
            return 'boolean'
        elif 'object' in dtype_lower:
            return 'string'
        else:
            return 'string'

    def _get_statistics(self, df: pd.DataFrame) -> dict:
        """Get basic statistics for numeric columns."""
        stats = {}
        numeric_cols = df.select_dtypes(include=['number']).columns

        for col in numeric_cols:
            try:
                col_stats = {
                    "min": float(df[col].min()) if pd.notna(df[col].min()) else None,
                    "max": float(df[col].max()) if pd.notna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if pd.notna(df[col].mean()) else None,
                    "sum": float(df[col].sum()) if pd.notna(df[col].sum()) else None,
                    "std": float(df[col].std()) if pd.notna(df[col].std()) else None
                }
                stats[str(col)] = col_stats
            except Exception:
                continue

        return stats

    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file content."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()[:16]}"


# Singleton instance
file_processor = FileProcessor()
