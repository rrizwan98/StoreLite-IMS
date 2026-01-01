"""
File Analysis Tools for Schema Agent - MCP Server Integration.

These function tools enable the Schema Agent to analyze uploaded files
by leveraging the Document MCP Server for professional file processing.

Features:
- PDF: Full text extraction, text search, metadata
- CSV: Read, filter, aggregate with statistics
- Excel: Multi-sheet support, filtering, aggregation
- Images: Metadata and dimensions

The tools automatically resolve file_id to actual file paths and call
the Document MCP Server tools for processing.

Version: 2.0.0 (MCP Integration)
Date: December 30, 2025
"""

import logging
from typing import Annotated, Literal, Optional
from pathlib import Path

from agents import function_tool

logger = logging.getLogger(__name__)


# Global context for user/db session (set by agent before tool call)
_current_user_id: Optional[int] = None
_current_db_session = None


def set_file_analysis_context(user_id: int, db_session):
    """Set the context for file analysis operations."""
    global _current_user_id, _current_db_session
    _current_user_id = user_id
    _current_db_session = db_session


def clear_file_analysis_context():
    """Clear the file analysis context."""
    global _current_user_id, _current_db_session
    _current_user_id = None
    _current_db_session = None


async def _get_file_path(file_id: str) -> Optional[str]:
    """
    Resolve file_id to actual file path.

    Returns the storage_path from the database for the given file_id.
    """
    global _current_user_id, _current_db_session

    if not _current_user_id or not _current_db_session:
        return None

    try:
        from sqlalchemy import select, and_
        from app.models import UploadedFile

        stmt = select(UploadedFile).where(
            and_(
                UploadedFile.file_id == file_id,
                UploadedFile.user_id == _current_user_id,
                UploadedFile.status == 'ready',
                UploadedFile.deleted_at.is_(None)
            )
        )
        result = await _current_db_session.execute(stmt)
        file_record = result.scalar_one_or_none()

        if file_record and not file_record.is_expired:
            return file_record.storage_path

        return None
    except Exception as e:
        logger.error(f"[File Analysis] Error getting file path: {e}")
        return None


async def _get_file_info(file_id: str) -> Optional[dict]:
    """Get file metadata from database."""
    global _current_user_id, _current_db_session

    if not _current_user_id or not _current_db_session:
        return None

    try:
        from sqlalchemy import select, and_
        from app.models import UploadedFile

        stmt = select(UploadedFile).where(
            and_(
                UploadedFile.file_id == file_id,
                UploadedFile.user_id == _current_user_id,
                UploadedFile.deleted_at.is_(None)
            )
        )
        result = await _current_db_session.execute(stmt)
        file_record = result.scalar_one_or_none()

        if file_record:
            return {
                "file_id": file_record.file_id,
                "file_name": file_record.file_name,
                "file_type": file_record.file_type,
                "file_size": file_record.file_size,
                "status": file_record.status,
                "storage_path": file_record.storage_path,
                "is_expired": file_record.is_expired,
                "processed_data": file_record.processed_data
            }

        return None
    except Exception as e:
        logger.error(f"[File Analysis] Error getting file info: {e}")
        return None


# =============================================================================
# PDF Tools
# =============================================================================

@function_tool
async def pdf_read_text(
    file_id: Annotated[str, "The unique file_id of the uploaded PDF file"],
    pages: Annotated[Optional[str], "Optional: comma-separated page numbers (e.g., '1,2,5'). Leave empty to read ALL pages."] = None
) -> str:
    """
    Read and extract ALL text content from a PDF file.

    This tool extracts the complete text content from every page of the PDF,
    including text from tables. Use this tool FIRST when a user uploads a PDF
    and asks ANY question about its content.

    IMPORTANT: This tool reads the ENTIRE PDF - you do NOT need page numbers
    unless the user specifically asks for certain pages. Always use this tool
    to read the full document before answering questions.

    Args:
        file_id: The uploaded file's unique identifier
        pages: Optional specific pages to read (e.g., "1,5,10"). Default: ALL pages.

    Returns:
        Complete text content from all pages, including tables.

    Examples:
        - User asks "What is in this PDF?" -> Call pdf_read_text(file_id) with no pages
        - User asks "Summarize the document" -> Call pdf_read_text(file_id) to get all text
        - User asks "What's on page 5?" -> Call pdf_read_text(file_id, pages="5")
    """
    logger.info(f"[PDF Read] file_id={file_id[:8]}..., pages={pages}")

    file_path = await _get_file_path(file_id)
    if not file_path:
        return "Error: File not found or not ready. Please ensure the file was uploaded successfully."

    try:
        # Import document processing functions
        from app.mcp_server.document_server import extract_pdf_text

        # Parse pages if provided
        page_list = None
        if pages:
            try:
                page_list = [int(p.strip()) for p in pages.split(",")]
            except ValueError:
                return "Error: Invalid page format. Use comma-separated numbers like '1,2,5'"

        result = extract_pdf_text(file_path, page_list)

        if "error" in result:
            return f"Error reading PDF: {result['error']}"

        # Format output
        output = []
        output.append(f"## PDF Content: {Path(file_path).name}")
        output.append(f"**Total Pages:** {result['total_pages']}")
        output.append(f"**Text Length:** {result.get('total_text_length', 0)} characters\n")

        # Include full text for agent to analyze
        if result.get('full_text'):
            output.append("### Document Text:\n")
            output.append(result['full_text'][:50000])  # Limit to 50K chars

            if result.get('total_text_length', 0) > 50000:
                output.append(f"\n\n[Text truncated. Total: {result['total_text_length']} chars]")

        # Include table summaries
        total_tables = sum(len(p.get('tables', [])) for p in result.get('pages', []))
        if total_tables > 0:
            output.append(f"\n### Tables Found: {total_tables}")
            for page in result.get('pages', []):
                for i, table in enumerate(page.get('tables', [])):
                    output.append(f"\n**Table on Page {page['page_number']}:**")
                    output.append(f"Headers: {', '.join(table.get('headers', []))}")
                    output.append(f"Rows: {len(table.get('rows', []))}")

        return "\n".join(output)

    except Exception as e:
        logger.error(f"[PDF Read] Error: {e}", exc_info=True)
        return f"Error processing PDF: {str(e)}"


@function_tool
async def pdf_search_text(
    file_id: Annotated[str, "The unique file_id of the uploaded PDF file"],
    query: Annotated[str, "The text to search for in the PDF (word, phrase, or partial text)"],
    case_sensitive: Annotated[bool, "Whether to match case exactly"] = False
) -> str:
    """
    Search for specific text within a PDF file.

    This tool searches through ALL pages of the PDF and returns every location
    where the search term appears, along with the surrounding context.

    Use this when:
    - User asks to find specific information (e.g., "find revenue figures")
    - User asks about a specific topic (e.g., "what does it say about Q4?")
    - User wants to locate where something is mentioned

    Args:
        file_id: The uploaded file's unique identifier
        query: The text to search for (can be a word, phrase, or partial text)
        case_sensitive: Whether to match exact case (default: False)

    Returns:
        All matches with page numbers, line context, and match count.

    Examples:
        - "Find revenue" -> pdf_search_text(file_id, "revenue")
        - "Where is profit mentioned?" -> pdf_search_text(file_id, "profit")
        - "Find 'Segment Operating Performance'" -> pdf_search_text(file_id, "Segment Operating Performance")
    """
    logger.info(f"[PDF Search] file_id={file_id[:8]}..., query='{query}'")

    file_path = await _get_file_path(file_id)
    if not file_path:
        return "Error: File not found or not ready."

    try:
        from app.mcp_server.document_server import search_pdf_text

        result = search_pdf_text(file_path, query, case_sensitive)

        if "error" in result:
            return f"Error searching PDF: {result['error']}"

        # Format output
        output = []
        output.append(f"## Search Results for: '{query}'")
        output.append(f"**Total Matches:** {result['total_matches']}")
        output.append(f"**Pages with Matches:** {result['pages_with_matches']}\n")

        if result['total_matches'] == 0:
            output.append(f"No matches found for '{query}' in this PDF.")
            output.append("Try a different search term or check spelling.")
        else:
            output.append("### Matches:\n")
            for match in result.get('matches', [])[:30]:  # Show first 30 matches
                output.append(f"**Page {match['page']}, Line {match['line_number']}:**")
                output.append(f"  {match['matched_line']}")
                output.append(f"  *Context:* {match['context'][:300]}\n")

        return "\n".join(output)

    except Exception as e:
        logger.error(f"[PDF Search] Error: {e}", exc_info=True)
        return f"Error searching PDF: {str(e)}"


@function_tool
async def pdf_get_info(
    file_id: Annotated[str, "The unique file_id of the uploaded PDF file"]
) -> str:
    """
    Get PDF file metadata (page count, author, title, file size).

    Use this to quickly check what a PDF contains before reading it fully.

    Args:
        file_id: The uploaded file's unique identifier

    Returns:
        Page count, document metadata, and file information.
    """
    logger.info(f"[PDF Info] file_id={file_id[:8]}...")

    file_path = await _get_file_path(file_id)
    if not file_path:
        return "Error: File not found or not ready."

    try:
        from app.mcp_server.document_server import get_pdf_metadata

        result = get_pdf_metadata(file_path)

        if "error" in result:
            return f"Error getting PDF info: {result['error']}"

        # Format output
        output = []
        output.append(f"## PDF Information")
        output.append(f"**File:** {Path(file_path).name}")
        output.append(f"**Pages:** {result['page_count']}")
        output.append(f"**Size:** {result['file_size_bytes'] / 1024:.1f} KB")

        meta = result.get('metadata', {})
        if meta.get('title'):
            output.append(f"**Title:** {meta['title']}")
        if meta.get('author'):
            output.append(f"**Author:** {meta['author']}")
        if meta.get('subject'):
            output.append(f"**Subject:** {meta['subject']}")

        return "\n".join(output)

    except Exception as e:
        logger.error(f"[PDF Info] Error: {e}", exc_info=True)
        return f"Error getting PDF info: {str(e)}"


# =============================================================================
# CSV/Excel Tools
# =============================================================================

@function_tool
async def data_read(
    file_id: Annotated[str, "The unique file_id of the uploaded CSV or Excel file"],
    limit: Annotated[int, "Maximum number of rows to return"] = 100,
    sheet_name: Annotated[Optional[str], "For Excel files: specific sheet name to read"] = None
) -> str:
    """
    Read data from a CSV or Excel file.

    Returns column information, statistics, and data rows.
    Use this to understand the structure and content of uploaded data files.

    Args:
        file_id: The uploaded file's unique identifier
        limit: Maximum rows to return (default: 100)
        sheet_name: For Excel files, specific sheet to read (default: first sheet)

    Returns:
        Column names, data types, statistics, and sample data rows.
    """
    logger.info(f"[Data Read] file_id={file_id[:8]}..., limit={limit}")

    file_info = await _get_file_info(file_id)
    if not file_info:
        return "Error: File not found."

    if file_info.get('status') != 'ready':
        return f"Error: File is still processing. Status: {file_info.get('status')}"

    file_path = file_info.get('storage_path')
    file_type = file_info.get('file_type')

    try:
        from app.mcp_server.document_server import read_csv_file, read_excel_file

        if file_type == 'csv':
            result = read_csv_file(file_path, limit)
        elif file_type == 'excel':
            result = read_excel_file(file_path, sheet_name, limit)
        else:
            return f"Error: File type '{file_type}' is not a data file. Use pdf_read_text for PDFs."

        if "error" in result:
            return f"Error reading file: {result['error']}"

        # Format output
        output = []
        output.append(f"## Data File: {file_info.get('file_name')}")
        output.append(f"**Total Rows:** {result.get('total_rows', 'N/A')}")
        output.append(f"**Columns:** {result.get('column_count', 0)}")

        if file_type == 'excel' and result.get('sheet_names'):
            output.append(f"**Sheets:** {', '.join(result['sheet_names'])}")
            output.append(f"**Active Sheet:** {result.get('active_sheet')}")

        # Column info
        output.append("\n### Columns:")
        for col in result.get('columns', [])[:20]:
            sample = col.get('sample', 'N/A')
            if sample and len(str(sample)) > 50:
                sample = str(sample)[:50] + "..."
            output.append(f"- **{col['name']}** ({col.get('type', 'unknown')}): e.g., `{sample}`")

        # Statistics
        stats = result.get('statistics', {})
        if stats:
            output.append("\n### Numeric Statistics:")
            for col_name, col_stats in list(stats.items())[:5]:
                output.append(f"- **{col_name}**: min={col_stats.get('min'):.2f}, max={col_stats.get('max'):.2f}, sum={col_stats.get('sum'):.2f}")

        # Sample data
        data = result.get('data', [])
        if data:
            output.append(f"\n### Sample Data ({len(data)} rows):")
            for i, row in enumerate(data[:10], 1):
                row_preview = ", ".join([f"{k}: {str(v)[:30]}" for k, v in list(row.items())[:5]])
                output.append(f"{i}. {row_preview}")

        return "\n".join(output)

    except Exception as e:
        logger.error(f"[Data Read] Error: {e}", exc_info=True)
        return f"Error reading data file: {str(e)}"


@function_tool
async def data_filter(
    file_id: Annotated[str, "The unique file_id of the uploaded CSV or Excel file"],
    column: Annotated[str, "Column name to filter on"],
    operator: Annotated[Literal["equals", "contains", "greater_than", "less_than", "not_equals"], "Filter operator"],
    value: Annotated[str, "Value to compare against"]
) -> str:
    """
    Filter data from a CSV or Excel file by a column condition.

    Use this to find specific rows matching criteria.

    Args:
        file_id: The uploaded file's unique identifier
        column: Column name to filter on
        operator: One of: equals, contains, greater_than, less_than, not_equals
        value: Value to compare against

    Returns:
        Rows matching the filter condition.

    Examples:
        - Find active users: data_filter(file_id, "status", "equals", "active")
        - Find sales > 1000: data_filter(file_id, "amount", "greater_than", "1000")
        - Find emails containing 'gmail': data_filter(file_id, "email", "contains", "gmail")
    """
    logger.info(f"[Data Filter] file_id={file_id[:8]}..., {column} {operator} {value}")

    file_path = await _get_file_path(file_id)
    if not file_path:
        return "Error: File not found or not ready."

    try:
        from app.mcp_server.document_server import filter_tabular_data

        result = filter_tabular_data(file_path, column, operator, value)

        if "error" in result:
            return f"Error filtering data: {result['error']}"

        # Format output
        output = []
        output.append(f"## Filter Results")
        output.append(f"**Filter:** {column} {operator} '{value}'")
        output.append(f"**Original Rows:** {result.get('original_rows', 0)}")
        output.append(f"**Filtered Rows:** {result.get('filtered_rows', 0)}")

        data = result.get('data', [])
        if data:
            output.append(f"\n### Matching Rows ({len(data)}):")
            for i, row in enumerate(data[:20], 1):
                row_str = ", ".join([f"{k}: {v}" for k, v in list(row.items())[:6]])
                output.append(f"{i}. {row_str}")
        else:
            output.append("\nNo rows match this filter condition.")

        return "\n".join(output)

    except Exception as e:
        logger.error(f"[Data Filter] Error: {e}", exc_info=True)
        return f"Error filtering data: {str(e)}"


@function_tool
async def data_aggregate(
    file_id: Annotated[str, "The unique file_id of the uploaded CSV or Excel file"],
    column: Annotated[str, "Numeric column to aggregate"],
    operation: Annotated[Literal["sum", "avg", "count", "min", "max"], "Aggregation operation"]
) -> str:
    """
    Calculate aggregate statistics on a data column.

    Use this for calculations like totals, averages, counts.

    Args:
        file_id: The uploaded file's unique identifier
        column: Numeric column to aggregate
        operation: One of: sum, avg, count, min, max

    Returns:
        The calculated aggregate value.

    Examples:
        - Total sales: data_aggregate(file_id, "amount", "sum")
        - Average price: data_aggregate(file_id, "price", "avg")
        - Number of orders: data_aggregate(file_id, "order_id", "count")
    """
    logger.info(f"[Data Aggregate] file_id={file_id[:8]}..., {operation}({column})")

    file_path = await _get_file_path(file_id)
    if not file_path:
        return "Error: File not found or not ready."

    try:
        from app.mcp_server.document_server import aggregate_tabular_data

        result = aggregate_tabular_data(file_path, column, operation)

        if "error" in result:
            return f"Error aggregating data: {result['error']}"

        # Format output
        op_names = {"sum": "Sum", "avg": "Average", "count": "Count", "min": "Minimum", "max": "Maximum"}
        op_name = op_names.get(operation, operation.title())

        output = []
        output.append(f"## Aggregation Result")
        output.append(f"**Column:** {column}")
        output.append(f"**Operation:** {op_name}")
        output.append(f"**Result:** {result.get('result', 'N/A')}")
        output.append(f"**Rows Processed:** {result.get('rows_processed', 0)}")

        return "\n".join(output)

    except Exception as e:
        logger.error(f"[Data Aggregate] Error: {e}", exc_info=True)
        return f"Error aggregating data: {str(e)}"


# =============================================================================
# Image Tools
# =============================================================================

@function_tool
async def image_get_info(
    file_id: Annotated[str, "The unique file_id of the uploaded image file"]
) -> str:
    """
    Get image file metadata and dimensions.

    Args:
        file_id: The uploaded file's unique identifier

    Returns:
        Image dimensions, format, and file size.
    """
    logger.info(f"[Image Info] file_id={file_id[:8]}...")

    file_info = await _get_file_info(file_id)
    if not file_info:
        return "Error: File not found."

    if file_info.get('file_type') != 'image':
        return f"Error: File is not an image. Type: {file_info.get('file_type')}"

    file_path = file_info.get('storage_path')

    try:
        from app.mcp_server.document_server import get_image_info

        result = get_image_info(file_path, include_base64=False)

        if "error" in result:
            return f"Error getting image info: {result['error']}"

        output = []
        output.append(f"## Image Information")
        output.append(f"**File:** {file_info.get('file_name')}")
        output.append(f"**Dimensions:** {result.get('width')} x {result.get('height')} pixels")
        output.append(f"**Format:** {result.get('format')}")
        output.append(f"**Color Mode:** {result.get('mode')}")
        output.append(f"**Size:** {result.get('file_size_bytes', 0) / 1024:.1f} KB")

        return "\n".join(output)

    except Exception as e:
        logger.error(f"[Image Info] Error: {e}", exc_info=True)
        return f"Error getting image info: {str(e)}"


@function_tool
async def get_uploaded_file_info(
    file_id: Annotated[str, "The unique identifier of the uploaded file"]
) -> str:
    """
    Get metadata and status of an uploaded file.

    Use this to check:
    - If a file is ready for analysis
    - File type (PDF, CSV, Excel, Image)
    - File name and size

    Args:
        file_id: The uploaded file identifier

    Returns:
        File metadata including name, type, size, and processing status.
    """
    logger.info(f"[File Info] file_id={file_id[:8]}...")

    file_info = await _get_file_info(file_id)

    if not file_info:
        return f"Error: File not found. File ID: {file_id}"

    if file_info.get('is_expired'):
        return f"Error: File has expired and is no longer available."

    output = []
    output.append(f"## File Information")
    output.append(f"**Name:** {file_info.get('file_name')}")
    output.append(f"**Type:** {file_info.get('file_type', 'unknown').upper()}")
    output.append(f"**Size:** {file_info.get('file_size', 0) / 1024:.1f} KB")
    output.append(f"**Status:** {file_info.get('status')}")

    # Add type-specific guidance
    file_type = file_info.get('file_type')
    if file_type == 'pdf':
        output.append("\n**Available Tools for this PDF:**")
        output.append("- `pdf_read_text`: Read all text content")
        output.append("- `pdf_search_text`: Search for specific text")
        output.append("- `pdf_get_info`: Get page count and metadata")
    elif file_type in ['csv', 'excel']:
        output.append("\n**Available Tools for this data file:**")
        output.append("- `data_read`: Read columns and rows")
        output.append("- `data_filter`: Filter by column conditions")
        output.append("- `data_aggregate`: Calculate sum, avg, etc.")
    elif file_type == 'image':
        output.append("\n**Available Tools for this image:**")
        output.append("- `image_get_info`: Get dimensions and format")

    return "\n".join(output)


# =============================================================================
# Export Tools
# =============================================================================

FILE_ANALYSIS_TOOLS = [
    # PDF Tools
    pdf_read_text,
    pdf_search_text,
    pdf_get_info,
    # Data Tools
    data_read,
    data_filter,
    data_aggregate,
    # Image Tools
    image_get_info,
    # General
    get_uploaded_file_info,
]

__all__ = [
    "pdf_read_text",
    "pdf_search_text",
    "pdf_get_info",
    "data_read",
    "data_filter",
    "data_aggregate",
    "image_get_info",
    "get_uploaded_file_info",
    "FILE_ANALYSIS_TOOLS",
    "set_file_analysis_context",
    "clear_file_analysis_context",
]
