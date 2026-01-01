"""
Google Drive Connector Sub-Agent.

Specialized agent for handling all Google Drive operations.
This agent uses the Google Drive API via OAuth tokens to
search, read, and list files from the user's Google Drive.
"""

import json
import logging
import httpx
from typing import List, Dict, Any

from agents.tool import FunctionTool

from .base import BaseConnectorAgent

logger = logging.getLogger(__name__)

# Google Drive API endpoints
GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3"
GOOGLE_DOCS_API = "https://docs.googleapis.com/v1/documents"
GOOGLE_SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"


class GoogleDriveConnectorAgent(BaseConnectorAgent):
    """
    Specialized agent for Google Drive operations.

    Handles:
    - Searching files in Google Drive
    - Reading file contents
    - Listing files and folders
    - Getting file metadata
    - Reading Google Docs, Sheets, and Slides content

    This agent uses direct Google API calls with the stored OAuth token.
    """

    CONNECTOR_TYPE = "GoogleDrive"
    TOOL_NAME = "google_drive_connector"
    TOOL_DESCRIPTION = (
        "Handle ALL Google Drive operations including: "
        "searching files, reading file contents, listing files, "
        "reading Google Docs, Sheets, and Slides. "
        "Use this for ANY Google Drive-related task."
    )

    def get_system_prompt(self) -> str:
        """Get Google Drive-specific system prompt."""
        return """You are a Google Drive Expert Agent. Your job is to execute Google Drive operations using the available tools.

## AUTONOMOUS EXECUTION
Execute tasks immediately. Make intelligent decisions based on the content and context.
- Need to find a file? → Search with relevant keywords
- Need file content? → Get the file and read it
- Need a list of files? → Use list_files with appropriate filters

Execute, don't ask unnecessary questions.

## YOUR CAPABILITIES
- Search for files by name, type, or content
- List files in Drive or specific folders
- Read file contents (Google Docs, Sheets, text files)
- Get file metadata (name, size, modified date, owner)
- Navigate folder structures

## FILE TYPES YOU CAN READ
- Google Docs: Full text content
- Google Sheets: Cell data as structured content
- Google Slides: Text content from slides
- Text files: Plain text content
- PDF files: Text extraction
- Other files: Metadata only

## TERMINOLOGY
- "Drive" = Google Drive (the cloud storage)
- "Doc" or "Document" = Google Docs (word processor)
- "Sheet" or "Spreadsheet" = Google Sheets
- "Slides" or "Presentation" = Google Slides
- "Folder" = Directory in Drive

## EXECUTION RULES

1. ALWAYS USE TOOLS - Never pretend to complete operations without calling tools
2. SEARCH FIRST - If user asks about a file, search to find it
3. CHAIN OPERATIONS - Find file → Get content automatically
4. REPORT RESULTS - Confirm what was found with specific details

## WORKFLOW: FIND AND READ A FILE

Step 1: Search for the file
```
gdrive_search with query="filename or keywords"
```

Step 2: Get file content (if found)
```
gdrive_read_file with file_id from search results
```

## WORKFLOW: LIST FILES

Step 1: List files with optional filters
```
gdrive_list_files with folder_id (optional) and mime_type (optional)
```

## ERROR HANDLING
If a file is not found:
- Try broader search terms
- Check if user specified a folder
- Report what was searched

If content cannot be read:
- Report the file type
- Explain what can/cannot be read

## RESPONSE FORMAT
After completing operations, provide:
- What was found/done
- File names and relevant details
- Content summary if reading files
- Errors if any occurred

Execute tasks completely using tools."""

    async def load_tools(self) -> List[FunctionTool]:
        """Load Google Drive tools."""
        logger.info(f"[GoogleDriveAgent] Loading tools with OAuth token")

        # Get access token from auth config
        access_token = self.auth_config.get("access_token")
        if not access_token:
            logger.error("[GoogleDriveAgent] No access token in auth config!")
            return []

        # Create tools with the access token
        tools = [
            self._create_search_tool(access_token),
            self._create_list_files_tool(access_token),
            self._create_read_file_tool(access_token),
            self._create_get_file_info_tool(access_token),
        ]

        logger.info(f"[GoogleDriveAgent] Created {len(tools)} tools")
        return tools

    def _create_search_tool(self, access_token: str) -> FunctionTool:
        """Create the search files tool."""

        async def gdrive_search(ctx, args: str) -> str:
            """Search for files in Google Drive."""
            try:
                kwargs = json.loads(args) if args else {}
                query = kwargs.get("query", "")

                if not query:
                    return "[GoogleDrive:gdrive_search] Error: query parameter is required"

                logger.info(f"[GoogleDriveAgent] Searching for: {query}")

                # Build Drive API query
                # Search in file name and full text
                drive_query = f"name contains '{query}' or fullText contains '{query}'"

                params = {
                    "q": drive_query,
                    "fields": "files(id,name,mimeType,modifiedTime,size,owners)",
                    "pageSize": 20,
                    "orderBy": "modifiedTime desc",
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{GOOGLE_DRIVE_API}/files",
                        params=params,
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    if response.status_code != 200:
                        error_msg = f"API error: {response.status_code} - {response.text}"
                        logger.error(f"[GoogleDriveAgent] {error_msg}")
                        return f"[GoogleDrive:gdrive_search] Error: {error_msg}"

                    data = response.json()
                    files = data.get("files", [])

                    if not files:
                        return f"[GoogleDrive:gdrive_search] No files found matching '{query}'"

                    # Format results
                    results = []
                    for f in files:
                        file_type = self._get_readable_type(f.get("mimeType", ""))
                        size = self._format_size(f.get("size"))
                        modified = f.get("modifiedTime", "")[:10]  # Just date
                        results.append(
                            f"- {f['name']} (ID: {f['id']})\n"
                            f"  Type: {file_type}, Modified: {modified}, Size: {size}"
                        )

                    return f"[GoogleDrive:gdrive_search] Found {len(files)} files:\n" + "\n".join(results)

            except Exception as e:
                error_msg = f"[GoogleDrive:gdrive_search] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gdrive_search.__name__ = "gdrive_search"
        gdrive_search.__doc__ = "Search for files in Google Drive by name or content"

        return FunctionTool(
            name="gdrive_search",
            description="Search for files in Google Drive. Returns file names, IDs, and metadata.",
            params_json_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (file name or content to search for)"
                    }
                },
                "required": ["query"]
            },
            on_invoke_tool=gdrive_search,
            strict_json_schema=False,
        )

    def _create_list_files_tool(self, access_token: str) -> FunctionTool:
        """Create the list files tool."""

        async def gdrive_list_files(ctx, args: str) -> str:
            """List files in Google Drive."""
            try:
                kwargs = json.loads(args) if args else {}
                folder_id = kwargs.get("folder_id", "root")
                mime_type = kwargs.get("mime_type")
                page_size = kwargs.get("page_size", 25)

                logger.info(f"[GoogleDriveAgent] Listing files in folder: {folder_id}")

                # Build query
                query_parts = [f"'{folder_id}' in parents", "trashed=false"]
                if mime_type:
                    query_parts.append(f"mimeType='{mime_type}'")

                params = {
                    "q": " and ".join(query_parts),
                    "fields": "files(id,name,mimeType,modifiedTime,size)",
                    "pageSize": page_size,
                    "orderBy": "name",
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{GOOGLE_DRIVE_API}/files",
                        params=params,
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    if response.status_code != 200:
                        error_msg = f"API error: {response.status_code} - {response.text}"
                        logger.error(f"[GoogleDriveAgent] {error_msg}")
                        return f"[GoogleDrive:gdrive_list_files] Error: {error_msg}"

                    data = response.json()
                    files = data.get("files", [])

                    if not files:
                        return f"[GoogleDrive:gdrive_list_files] No files found in folder"

                    # Separate folders and files
                    folders = [f for f in files if f.get("mimeType") == "application/vnd.google-apps.folder"]
                    regular_files = [f for f in files if f.get("mimeType") != "application/vnd.google-apps.folder"]

                    results = []

                    if folders:
                        results.append("Folders:")
                        for f in folders:
                            results.append(f"  [Folder] {f['name']} (ID: {f['id']})")

                    if regular_files:
                        results.append("Files:")
                        for f in regular_files:
                            file_type = self._get_readable_type(f.get("mimeType", ""))
                            size = self._format_size(f.get("size"))
                            results.append(f"  {f['name']} ({file_type}, {size}) - ID: {f['id']}")

                    return f"[GoogleDrive:gdrive_list_files] Found {len(files)} items:\n" + "\n".join(results)

            except Exception as e:
                error_msg = f"[GoogleDrive:gdrive_list_files] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gdrive_list_files.__name__ = "gdrive_list_files"
        gdrive_list_files.__doc__ = "List files in a Google Drive folder"

        return FunctionTool(
            name="gdrive_list_files",
            description="List files in Google Drive. Optionally specify a folder ID and mime type filter.",
            params_json_schema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Folder ID to list (default: 'root' for My Drive)"
                    },
                    "mime_type": {
                        "type": "string",
                        "description": "Optional MIME type filter (e.g., 'application/vnd.google-apps.document')"
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of files to return (default: 25)"
                    }
                },
                "required": []
            },
            on_invoke_tool=gdrive_list_files,
            strict_json_schema=False,
        )

    def _create_read_file_tool(self, access_token: str) -> FunctionTool:
        """Create the read file tool."""

        async def gdrive_read_file(ctx, args: str) -> str:
            """Read file contents from Google Drive."""
            try:
                kwargs = json.loads(args) if args else {}
                file_id = kwargs.get("file_id", "")

                if not file_id:
                    return "[GoogleDrive:gdrive_read_file] Error: file_id parameter is required"

                logger.info(f"[GoogleDriveAgent] Reading file: {file_id}")

                async with httpx.AsyncClient(timeout=60.0) as client:
                    # First, get file metadata to determine type
                    meta_response = await client.get(
                        f"{GOOGLE_DRIVE_API}/files/{file_id}",
                        params={"fields": "id,name,mimeType,size"},
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    if meta_response.status_code != 200:
                        error_msg = f"Cannot access file: {meta_response.status_code}"
                        return f"[GoogleDrive:gdrive_read_file] Error: {error_msg}"

                    file_meta = meta_response.json()
                    mime_type = file_meta.get("mimeType", "")
                    file_name = file_meta.get("name", "unknown")

                    logger.info(f"[GoogleDriveAgent] File type: {mime_type}")

                    # Handle different file types
                    content = ""

                    if mime_type == "application/vnd.google-apps.document":
                        # Google Docs - export as plain text
                        export_response = await client.get(
                            f"{GOOGLE_DRIVE_API}/files/{file_id}/export",
                            params={"mimeType": "text/plain"},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        if export_response.status_code == 200:
                            content = export_response.text
                        else:
                            content = f"[Could not export Google Doc: {export_response.status_code}]"

                    elif mime_type == "application/vnd.google-apps.spreadsheet":
                        # Google Sheets - export as CSV
                        export_response = await client.get(
                            f"{GOOGLE_DRIVE_API}/files/{file_id}/export",
                            params={"mimeType": "text/csv"},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        if export_response.status_code == 200:
                            content = export_response.text
                        else:
                            content = f"[Could not export Google Sheet: {export_response.status_code}]"

                    elif mime_type == "application/vnd.google-apps.presentation":
                        # Google Slides - export as text
                        export_response = await client.get(
                            f"{GOOGLE_DRIVE_API}/files/{file_id}/export",
                            params={"mimeType": "text/plain"},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        if export_response.status_code == 200:
                            content = export_response.text
                        else:
                            content = f"[Could not export Google Slides: {export_response.status_code}]"

                    elif mime_type.startswith("text/"):
                        # Text files - download directly
                        download_response = await client.get(
                            f"{GOOGLE_DRIVE_API}/files/{file_id}",
                            params={"alt": "media"},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        if download_response.status_code == 200:
                            content = download_response.text
                        else:
                            content = f"[Could not download text file: {download_response.status_code}]"

                    elif mime_type == "application/pdf":
                        # PDF files - note that we can't extract text without additional processing
                        content = "[PDF file - text extraction not available. Use file metadata instead.]"

                    else:
                        # Other files - binary, not readable as text
                        file_type = self._get_readable_type(mime_type)
                        content = f"[{file_type} file - binary content cannot be displayed as text]"

                    # Truncate very long content
                    if len(content) > 50000:
                        content = content[:50000] + "\n\n[Content truncated - file is very large]"

                    return f"[GoogleDrive:gdrive_read_file] File: {file_name}\nType: {self._get_readable_type(mime_type)}\n\nContent:\n{content}"

            except Exception as e:
                error_msg = f"[GoogleDrive:gdrive_read_file] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gdrive_read_file.__name__ = "gdrive_read_file"
        gdrive_read_file.__doc__ = "Read contents of a file from Google Drive"

        return FunctionTool(
            name="gdrive_read_file",
            description="Read the contents of a file from Google Drive. Supports Google Docs, Sheets, Slides, and text files.",
            params_json_schema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The Google Drive file ID (obtained from search or list)"
                    }
                },
                "required": ["file_id"]
            },
            on_invoke_tool=gdrive_read_file,
            strict_json_schema=False,
        )

    def _create_get_file_info_tool(self, access_token: str) -> FunctionTool:
        """Create the get file info tool."""

        async def gdrive_get_file_info(ctx, args: str) -> str:
            """Get detailed information about a file."""
            try:
                kwargs = json.loads(args) if args else {}
                file_id = kwargs.get("file_id", "")

                if not file_id:
                    return "[GoogleDrive:gdrive_get_file_info] Error: file_id parameter is required"

                logger.info(f"[GoogleDriveAgent] Getting info for file: {file_id}")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{GOOGLE_DRIVE_API}/files/{file_id}",
                        params={
                            "fields": "id,name,mimeType,modifiedTime,createdTime,size,owners,shared,webViewLink,description"
                        },
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    if response.status_code != 200:
                        error_msg = f"Cannot access file: {response.status_code} - {response.text}"
                        return f"[GoogleDrive:gdrive_get_file_info] Error: {error_msg}"

                    file_info = response.json()

                    # Format the response
                    result_parts = [
                        f"Name: {file_info.get('name', 'Unknown')}",
                        f"ID: {file_info.get('id', 'Unknown')}",
                        f"Type: {self._get_readable_type(file_info.get('mimeType', ''))}",
                        f"Size: {self._format_size(file_info.get('size'))}",
                        f"Created: {file_info.get('createdTime', 'Unknown')[:10]}",
                        f"Modified: {file_info.get('modifiedTime', 'Unknown')[:10]}",
                        f"Shared: {'Yes' if file_info.get('shared') else 'No'}",
                    ]

                    owners = file_info.get("owners", [])
                    if owners:
                        owner_names = [o.get("displayName", o.get("emailAddress", "Unknown")) for o in owners]
                        result_parts.append(f"Owner: {', '.join(owner_names)}")

                    if file_info.get("webViewLink"):
                        result_parts.append(f"Link: {file_info['webViewLink']}")

                    if file_info.get("description"):
                        result_parts.append(f"Description: {file_info['description']}")

                    return f"[GoogleDrive:gdrive_get_file_info]\n" + "\n".join(result_parts)

            except Exception as e:
                error_msg = f"[GoogleDrive:gdrive_get_file_info] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gdrive_get_file_info.__name__ = "gdrive_get_file_info"
        gdrive_get_file_info.__doc__ = "Get detailed information about a file"

        return FunctionTool(
            name="gdrive_get_file_info",
            description="Get detailed metadata about a file including name, type, size, owner, creation/modification dates.",
            params_json_schema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The Google Drive file ID"
                    }
                },
                "required": ["file_id"]
            },
            on_invoke_tool=gdrive_get_file_info,
            strict_json_schema=False,
        )

    def _get_readable_type(self, mime_type: str) -> str:
        """Convert MIME type to human-readable format."""
        type_map = {
            "application/vnd.google-apps.document": "Google Doc",
            "application/vnd.google-apps.spreadsheet": "Google Sheet",
            "application/vnd.google-apps.presentation": "Google Slides",
            "application/vnd.google-apps.folder": "Folder",
            "application/vnd.google-apps.form": "Google Form",
            "application/vnd.google-apps.drawing": "Google Drawing",
            "application/pdf": "PDF",
            "text/plain": "Text File",
            "text/csv": "CSV",
            "text/html": "HTML",
            "application/json": "JSON",
            "image/jpeg": "JPEG Image",
            "image/png": "PNG Image",
            "image/gif": "GIF Image",
            "video/mp4": "MP4 Video",
            "audio/mpeg": "MP3 Audio",
            "application/zip": "ZIP Archive",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Spreadsheet",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
        }
        return type_map.get(mime_type, mime_type.split("/")[-1].upper() if mime_type else "Unknown")

    def _format_size(self, size_bytes) -> str:
        """Format file size in human-readable format."""
        if not size_bytes:
            return "N/A"

        try:
            size = int(size_bytes)
            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except (ValueError, TypeError):
            return "N/A"
