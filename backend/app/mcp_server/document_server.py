"""
Document MCP Server - Professional file processing for Schema Agent.

This MCP server provides tools for reading, searching, and extracting content from:
- PDF files (full text extraction, page-by-page, table extraction)
- CSV files (read, filter, aggregate)
- Excel files (multi-sheet support)
- Images (OCR-ready, metadata)

Uses FastMCP for MCP protocol implementation.

Version: 1.0.0
Date: December 30, 2025
"""

import os
import io
import re
import base64
import logging
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = Path("uploads")


def create_document_server() -> FastMCP:
    """Create and configure Document MCP Server."""
    server = FastMCP("document-mcp-server")
    return server


# =============================================================================
# PDF Processing Functions
# =============================================================================

def extract_pdf_text(file_path: str, page_numbers: Optional[list[int]] = None) -> dict:
    """
    Extract text from PDF file.

    Args:
        file_path: Path to PDF file
        page_numbers: Optional list of specific pages (1-indexed). None = all pages.

    Returns:
        Dict with pages, text content, and metadata
    """
    try:
        import pdfplumber
    except ImportError:
        return {"error": "pdfplumber not installed. Run: pip install pdfplumber"}

    try:
        results = {
            "file_path": file_path,
            "pages": [],
            "total_pages": 0,
            "full_text": "",
            "extracted_at": datetime.utcnow().isoformat() + "Z"
        }

        with pdfplumber.open(file_path) as pdf:
            results["total_pages"] = len(pdf.pages)

            # Determine which pages to process
            if page_numbers:
                pages_to_process = [(i-1, pdf.pages[i-1]) for i in page_numbers if 0 < i <= len(pdf.pages)]
            else:
                # Process all pages (limit to 100 for performance)
                pages_to_process = [(i, page) for i, page in enumerate(pdf.pages[:100])]

            all_text = []

            for page_idx, page in pages_to_process:
                page_num = page_idx + 1

                # Extract text
                text = page.extract_text() or ""

                # Extract tables
                tables = []
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 1:
                        headers = [str(h) if h else f"Col_{j}" for j, h in enumerate(table[0])]
                        rows = [[str(cell) if cell else "" for cell in row] for row in table[1:]]
                        tables.append({
                            "headers": headers,
                            "rows": rows[:50]  # Limit rows per table
                        })

                page_data = {
                    "page_number": page_num,
                    "text": text,
                    "text_length": len(text),
                    "tables": tables,
                    "table_count": len(tables)
                }

                results["pages"].append(page_data)
                all_text.append(f"--- Page {page_num} ---\n{text}")

            results["full_text"] = "\n\n".join(all_text)
            results["total_text_length"] = len(results["full_text"])

        return results

    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return {"error": str(e), "file_path": file_path}


def search_pdf_text(file_path: str, query: str, case_sensitive: bool = False) -> dict:
    """
    Search for text within a PDF file.

    Args:
        file_path: Path to PDF file
        query: Search term or phrase
        case_sensitive: Whether search is case sensitive

    Returns:
        Dict with matches, contexts, and page locations
    """
    try:
        import pdfplumber
    except ImportError:
        return {"error": "pdfplumber not installed"}

    try:
        matches = []
        total_match_count = 0

        with pdfplumber.open(file_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                text = page.extract_text() or ""

                # Prepare search
                search_text = text if case_sensitive else text.lower()
                search_query = query if case_sensitive else query.lower()

                # Find all occurrences
                lines = text.split('\n')
                search_lines = search_text.split('\n')

                for line_idx, (line, search_line) in enumerate(zip(lines, search_lines)):
                    if search_query in search_line:
                        # Get context (lines before and after)
                        context_start = max(0, line_idx - 1)
                        context_end = min(len(lines), line_idx + 2)
                        context = "\n".join(lines[context_start:context_end])

                        matches.append({
                            "page": page_num,
                            "line_number": line_idx + 1,
                            "matched_line": line.strip(),
                            "context": context.strip(),
                            "match_count": search_line.count(search_query)
                        })
                        total_match_count += search_line.count(search_query)

        return {
            "query": query,
            "file_path": file_path,
            "total_matches": total_match_count,
            "pages_with_matches": len(set(m["page"] for m in matches)),
            "matches": matches[:100],  # Limit results
            "case_sensitive": case_sensitive
        }

    except Exception as e:
        logger.error(f"PDF search error: {e}")
        return {"error": str(e), "query": query}


def get_pdf_metadata(file_path: str) -> dict:
    """Get PDF file metadata."""
    try:
        import pdfplumber
    except ImportError:
        return {"error": "pdfplumber not installed"}

    try:
        with pdfplumber.open(file_path) as pdf:
            metadata = pdf.metadata or {}
            return {
                "file_path": file_path,
                "page_count": len(pdf.pages),
                "metadata": {
                    "title": metadata.get("Title", ""),
                    "author": metadata.get("Author", ""),
                    "subject": metadata.get("Subject", ""),
                    "creator": metadata.get("Creator", ""),
                    "producer": metadata.get("Producer", ""),
                    "creation_date": metadata.get("CreationDate", ""),
                    "modification_date": metadata.get("ModDate", ""),
                },
                "file_size_bytes": os.path.getsize(file_path)
            }
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# CSV/Excel Processing Functions
# =============================================================================

def read_csv_file(file_path: str, limit: int = 1000, offset: int = 0) -> dict:
    """Read CSV file with pagination."""
    try:
        import pandas as pd
    except ImportError:
        return {"error": "pandas not installed"}

    try:
        # Try multiple encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            return {"error": "Could not decode CSV with supported encodings"}

        total_rows = len(df)
        df_slice = df.iloc[offset:offset + limit]

        # Column info
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            columns.append({
                "name": str(col),
                "type": dtype,
                "sample": str(df[col].dropna().iloc[0]) if len(df[col].dropna()) > 0 else None,
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique())
            })

        # Convert to records
        records = df_slice.fillna('').to_dict(orient='records')

        # Statistics for numeric columns
        stats = {}
        for col in df.select_dtypes(include=['number']).columns:
            try:
                stats[str(col)] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "sum": float(df[col].sum())
                }
            except:
                pass

        return {
            "file_path": file_path,
            "total_rows": total_rows,
            "returned_rows": len(records),
            "offset": offset,
            "columns": columns,
            "column_count": len(columns),
            "data": records,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"CSV read error: {e}")
        return {"error": str(e)}


def read_excel_file(file_path: str, sheet_name: Optional[str] = None, limit: int = 1000) -> dict:
    """Read Excel file with sheet selection."""
    try:
        import pandas as pd
    except ImportError:
        return {"error": "pandas not installed"}

    try:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names

        # Select sheet
        target_sheet = sheet_name if sheet_name and sheet_name in sheet_names else sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=target_sheet)

        total_rows = len(df)
        df_slice = df.head(limit)

        # Column info
        columns = []
        for col in df.columns:
            columns.append({
                "name": str(col),
                "type": str(df[col].dtype),
                "sample": str(df[col].dropna().iloc[0]) if len(df[col].dropna()) > 0 else None
            })

        records = df_slice.fillna('').to_dict(orient='records')

        return {
            "file_path": file_path,
            "sheet_names": sheet_names,
            "active_sheet": target_sheet,
            "total_rows": total_rows,
            "returned_rows": len(records),
            "columns": columns,
            "column_count": len(columns),
            "data": records
        }

    except Exception as e:
        logger.error(f"Excel read error: {e}")
        return {"error": str(e)}


def filter_tabular_data(file_path: str, column: str, operator: str, value: str) -> dict:
    """Filter CSV/Excel data by column condition."""
    try:
        import pandas as pd
    except ImportError:
        return {"error": "pandas not installed"}

    try:
        # Detect file type
        ext = Path(file_path).suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            return {"error": f"Unsupported file type: {ext}"}

        if column not in df.columns:
            return {"error": f"Column '{column}' not found. Available: {list(df.columns)}"}

        # Apply filter
        original_count = len(df)

        if operator == "equals":
            df = df[df[column].astype(str) == str(value)]
        elif operator == "contains":
            df = df[df[column].astype(str).str.contains(value, case=False, na=False)]
        elif operator == "greater_than":
            df = df[pd.to_numeric(df[column], errors='coerce') > float(value)]
        elif operator == "less_than":
            df = df[pd.to_numeric(df[column], errors='coerce') < float(value)]
        elif operator == "not_equals":
            df = df[df[column].astype(str) != str(value)]
        else:
            return {"error": f"Unknown operator: {operator}. Use: equals, contains, greater_than, less_than, not_equals"}

        records = df.head(100).fillna('').to_dict(orient='records')

        return {
            "file_path": file_path,
            "filter": {"column": column, "operator": operator, "value": value},
            "original_rows": original_count,
            "filtered_rows": len(df),
            "returned_rows": len(records),
            "data": records
        }

    except Exception as e:
        logger.error(f"Filter error: {e}")
        return {"error": str(e)}


def aggregate_tabular_data(file_path: str, column: str, operation: str) -> dict:
    """Aggregate data from a column (sum, avg, count, min, max)."""
    try:
        import pandas as pd
    except ImportError:
        return {"error": "pandas not installed"}

    try:
        ext = Path(file_path).suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            return {"error": f"Unsupported file type: {ext}"}

        if column not in df.columns:
            return {"error": f"Column '{column}' not found"}

        col_data = pd.to_numeric(df[column], errors='coerce').dropna()

        if operation == "sum":
            result = float(col_data.sum())
        elif operation == "avg" or operation == "mean":
            result = float(col_data.mean())
        elif operation == "count":
            result = int(len(col_data))
        elif operation == "min":
            result = float(col_data.min())
        elif operation == "max":
            result = float(col_data.max())
        elif operation == "std":
            result = float(col_data.std())
        else:
            return {"error": f"Unknown operation: {operation}. Use: sum, avg, count, min, max, std"}

        return {
            "file_path": file_path,
            "column": column,
            "operation": operation,
            "result": result,
            "rows_processed": len(col_data)
        }

    except Exception as e:
        logger.error(f"Aggregate error: {e}")
        return {"error": str(e)}


# =============================================================================
# Image Processing Functions
# =============================================================================

def get_image_info(file_path: str, include_base64: bool = False) -> dict:
    """Get image metadata and optionally base64 content."""
    try:
        from PIL import Image
    except ImportError:
        return {"error": "Pillow not installed. Run: pip install Pillow"}

    try:
        with Image.open(file_path) as img:
            result = {
                "file_path": file_path,
                "width": img.size[0],
                "height": img.size[1],
                "format": img.format,
                "mode": img.mode,
                "file_size_bytes": os.path.getsize(file_path)
            }

            if include_base64:
                buffer = io.BytesIO()
                save_format = img.format or 'PNG'
                if save_format.upper() == 'JPEG' and img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(buffer, format=save_format)
                b64 = base64.b64encode(buffer.getvalue()).decode()
                result["base64_content"] = f"data:image/{save_format.lower()};base64,{b64}"

            return result

    except Exception as e:
        logger.error(f"Image info error: {e}")
        return {"error": str(e)}


# =============================================================================
# MCP Server Registration
# =============================================================================

async def run_document_server():
    """Start the Document MCP server with HTTP transport."""
    server = create_document_server()

    # =========================================================================
    # PDF Tools
    # =========================================================================

    @server.tool()
    async def pdf_read(
        file_path: str,
        pages: str = None
    ) -> dict:
        """
        Read and extract text from a PDF file.

        This tool extracts ALL text content from PDF pages, including tables.
        Use this to read document content before answering questions.

        Args:
            file_path: Full path to the PDF file
            pages: Optional comma-separated page numbers (e.g., "1,2,5"). None = all pages.

        Returns:
            Full text content, page-by-page text, tables, and metadata.

        Example:
            pdf_read("/uploads/1/abc123.pdf") -> Returns all pages
            pdf_read("/uploads/1/abc123.pdf", pages="1,5,10") -> Returns specific pages
        """
        page_list = None
        if pages:
            try:
                page_list = [int(p.strip()) for p in pages.split(",")]
            except ValueError:
                return {"error": "Invalid page format. Use comma-separated numbers: 1,2,5"}

        return extract_pdf_text(file_path, page_list)

    @server.tool()
    async def pdf_search(
        file_path: str,
        query: str,
        case_sensitive: bool = False
    ) -> dict:
        """
        Search for specific text within a PDF file.

        Searches the ENTIRE PDF and returns all matching locations with context.
        Use this when user asks to find specific information in a PDF.

        Args:
            file_path: Full path to the PDF file
            query: Text to search for (word, phrase, or partial text)
            case_sensitive: Whether to match case exactly (default: False)

        Returns:
            All matches with page numbers, line numbers, and surrounding context.

        Example:
            pdf_search("/uploads/1/report.pdf", "revenue") -> Finds all "revenue" mentions
            pdf_search("/uploads/1/report.pdf", "Q4 Results", case_sensitive=True)
        """
        return search_pdf_text(file_path, query, case_sensitive)

    @server.tool()
    async def pdf_info(file_path: str) -> dict:
        """
        Get PDF file metadata (page count, author, title, etc.).

        Use this to get an overview of a PDF before reading its content.

        Args:
            file_path: Full path to the PDF file

        Returns:
            Page count, file size, and document metadata.
        """
        return get_pdf_metadata(file_path)

    # =========================================================================
    # CSV/Excel Tools
    # =========================================================================

    @server.tool()
    async def csv_read(
        file_path: str,
        limit: int = 1000,
        offset: int = 0
    ) -> dict:
        """
        Read a CSV file with column info and statistics.

        Args:
            file_path: Full path to the CSV file
            limit: Maximum rows to return (default: 1000)
            offset: Starting row for pagination (default: 0)

        Returns:
            Columns, data rows, row count, and numeric statistics.
        """
        return read_csv_file(file_path, limit, offset)

    @server.tool()
    async def excel_read(
        file_path: str,
        sheet_name: str = None,
        limit: int = 1000
    ) -> dict:
        """
        Read an Excel file with sheet selection.

        Args:
            file_path: Full path to the Excel file
            sheet_name: Specific sheet to read (default: first sheet)
            limit: Maximum rows to return (default: 1000)

        Returns:
            Sheet names, columns, data rows, and row count.
        """
        return read_excel_file(file_path, sheet_name, limit)

    @server.tool()
    async def data_filter(
        file_path: str,
        column: str,
        operator: str,
        value: str
    ) -> dict:
        """
        Filter CSV/Excel data by a column condition.

        Args:
            file_path: Full path to CSV or Excel file
            column: Column name to filter on
            operator: One of: equals, contains, greater_than, less_than, not_equals
            value: Value to compare against

        Returns:
            Filtered rows matching the condition.

        Example:
            data_filter("data.csv", "status", "equals", "active")
            data_filter("sales.xlsx", "amount", "greater_than", "1000")
        """
        return filter_tabular_data(file_path, column, operator, value)

    @server.tool()
    async def data_aggregate(
        file_path: str,
        column: str,
        operation: str
    ) -> dict:
        """
        Calculate aggregate statistics on a column.

        Args:
            file_path: Full path to CSV or Excel file
            column: Numeric column to aggregate
            operation: One of: sum, avg, count, min, max, std

        Returns:
            Aggregated result value.

        Example:
            data_aggregate("sales.csv", "amount", "sum") -> Total sales
            data_aggregate("products.xlsx", "price", "avg") -> Average price
        """
        return aggregate_tabular_data(file_path, column, operation)

    # =========================================================================
    # Image Tools
    # =========================================================================

    @server.tool()
    async def image_info(
        file_path: str,
        include_base64: bool = False
    ) -> dict:
        """
        Get image file metadata and dimensions.

        Args:
            file_path: Full path to the image file
            include_base64: Whether to include base64-encoded image content

        Returns:
            Width, height, format, mode, and file size.
        """
        return get_image_info(file_path, include_base64)

    # Run server with HTTP transport on port 8002
    logger.info("[Document MCP] Starting on port 8002...")
    await server.run_async(transport="sse", host="127.0.0.1", port=8002)


async def run_document_server_stdio():
    """Start the Document MCP server with stdio transport."""
    server = create_document_server()

    # Same tool registrations as HTTP version
    @server.tool()
    async def pdf_read(file_path: str, pages: str = None) -> dict:
        """Read and extract text from a PDF file. pages: comma-separated page numbers or None for all."""
        page_list = None
        if pages:
            try:
                page_list = [int(p.strip()) for p in pages.split(",")]
            except ValueError:
                return {"error": "Invalid page format"}
        return extract_pdf_text(file_path, page_list)

    @server.tool()
    async def pdf_search(file_path: str, query: str, case_sensitive: bool = False) -> dict:
        """Search for text within a PDF file. Returns matches with page numbers and context."""
        return search_pdf_text(file_path, query, case_sensitive)

    @server.tool()
    async def pdf_info(file_path: str) -> dict:
        """Get PDF file metadata (page count, author, title)."""
        return get_pdf_metadata(file_path)

    @server.tool()
    async def csv_read(file_path: str, limit: int = 1000, offset: int = 0) -> dict:
        """Read CSV file with pagination and statistics."""
        return read_csv_file(file_path, limit, offset)

    @server.tool()
    async def excel_read(file_path: str, sheet_name: str = None, limit: int = 1000) -> dict:
        """Read Excel file with sheet selection."""
        return read_excel_file(file_path, sheet_name, limit)

    @server.tool()
    async def data_filter(file_path: str, column: str, operator: str, value: str) -> dict:
        """Filter CSV/Excel data. Operators: equals, contains, greater_than, less_than, not_equals."""
        return filter_tabular_data(file_path, column, operator, value)

    @server.tool()
    async def data_aggregate(file_path: str, column: str, operation: str) -> dict:
        """Aggregate column data. Operations: sum, avg, count, min, max, std."""
        return aggregate_tabular_data(file_path, column, operation)

    @server.tool()
    async def image_info(file_path: str, include_base64: bool = False) -> dict:
        """Get image metadata (dimensions, format)."""
        return get_image_info(file_path, include_base64)

    await server.run_stdio_async()


if __name__ == "__main__":
    import sys
    import asyncio

    logging.basicConfig(level=logging.INFO)

    if "--stdio" in sys.argv:
        asyncio.run(run_document_server_stdio())
    else:
        asyncio.run(run_document_server())
