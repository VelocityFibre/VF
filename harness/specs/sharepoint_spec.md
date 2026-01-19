# SharePoint Agent Specification

## Purpose

Integrate FibreFlow with Microsoft SharePoint to enable automated document management, file synchronization, and team collaboration workflows. This agent provides seamless access to SharePoint Online sites for uploading contract documents, retrieving project files, and managing fiber infrastructure documentation.

## Domain

**Type**: External Integration
**Specialization**: Microsoft SharePoint Online API integration for document management
**External Service**: Microsoft Graph API / SharePoint REST API

## Capabilities

### 1. File Upload to SharePoint

**What it does**: Upload local files to specified SharePoint document libraries
**When to use**: Store contracts, BOQs, project documents, or reports to SharePoint
**Tool**: `upload_file_to_sharepoint`

**Use Cases**:
- Upload signed contractor agreements to "Contracts" library
- Store generated BOQ PDFs in project-specific folders
- Archive completed RFQ documentation

### 2. File Download from SharePoint

**What it does**: Download files from SharePoint to local filesystem or memory
**When to use**: Retrieve documents for processing, analysis, or distribution
**Tool**: `download_file_from_sharepoint`

**Use Cases**:
- Download contractor documentation for verification
- Fetch project templates for BOQ generation
- Retrieve historical data for analysis

### 3. List Files and Folders

**What it does**: Browse SharePoint document library contents
**When to use**: Discover available files, check for document existence, or audit storage
**Tool**: `list_sharepoint_contents`

**Use Cases**:
- Check if contractor has submitted required documents
- List all BOQs for a specific project
- Audit document storage for compliance

### 4. Create Folders

**What it does**: Create new folders in SharePoint document libraries
**When to use**: Organize documents by project, contractor, or category
**Tool**: `create_sharepoint_folder`

**Use Cases**:
- Create folder structure for new projects
- Organize contractor documents by company
- Set up BOQ/RFQ document hierarchies

### 5. Search Documents

**What it does**: Search SharePoint for documents by name, content, or metadata
**When to use**: Find specific documents across multiple libraries
**Tool**: `search_sharepoint_documents`

**Use Cases**:
- Find all documents mentioning a specific contractor
- Search for BOQs within a date range
- Locate project files by reference number

### 6. Get File Metadata

**What it does**: Retrieve file properties (size, modified date, author, etc.)
**When to use**: Verify document freshness or track changes
**Tool**: `get_file_metadata`

**Use Cases**:
- Check when contractor last updated their profile
- Verify document version timestamps
- Track who uploaded specific files

## Tools

### Tool: `upload_file_to_sharepoint`

**Purpose**: Upload file to SharePoint document library

**Parameters**:
- `local_file_path` (string, required): Path to local file to upload
- `sharepoint_library` (string, required): Target document library name (e.g., "Contracts")
- `sharepoint_folder` (string, optional): Target folder path within library (e.g., "Active/Contractor123")
- `overwrite` (boolean, optional): Overwrite if file exists (default: false)

**Returns**:
```json
{
  "status": "success",
  "file_url": "https://company.sharepoint.com/sites/fibreflow/Contracts/file.pdf",
  "file_id": "b!abc123...",
  "size_bytes": 15420,
  "uploaded_at": "2025-12-05T10:30:00Z"
}
```

**Example**:
```python
result = agent.execute_tool("upload_file_to_sharepoint", {
    "local_file_path": "/tmp/contract_signed.pdf",
    "sharepoint_library": "Contracts",
    "sharepoint_folder": "Active/VendorXYZ",
    "overwrite": False
})
```

**Error Handling**:
- File not found locally → `{"error": "file_not_found"}`
- Library doesn't exist → `{"error": "library_not_found"}`
- Insufficient permissions → `{"error": "access_denied"}`
- File already exists (overwrite=false) → `{"error": "file_exists"}`

### Tool: `download_file_from_sharepoint`

**Purpose**: Download file from SharePoint to local filesystem

**Parameters**:
- `file_url` (string, optional): SharePoint file URL
- `file_id` (string, optional): SharePoint file unique identifier
- `local_path` (string, required): Where to save downloaded file
- `overwrite` (boolean, optional): Overwrite local file if exists (default: false)

**Note**: Must provide either `file_url` OR `file_id`

**Returns**:
```json
{
  "status": "success",
  "local_path": "/tmp/downloaded_file.pdf",
  "size_bytes": 15420,
  "downloaded_at": "2025-12-05T10:35:00Z",
  "original_modified": "2025-12-01T09:15:00Z"
}
```

**Example**:
```python
result = agent.execute_tool("download_file_from_sharepoint", {
    "file_url": "https://company.sharepoint.com/sites/fibreflow/Contracts/file.pdf",
    "local_path": "/tmp/contract.pdf",
    "overwrite": True
})
```

### Tool: `list_sharepoint_contents`

**Purpose**: List files and folders in SharePoint library or folder

**Parameters**:
- `sharepoint_library` (string, required): Document library name
- `folder_path` (string, optional): Subfolder path (default: root)
- `recursive` (boolean, optional): Include subfolders (default: false)
- `file_types` (array, optional): Filter by extensions (e.g., ["pdf", "docx"])

**Returns**:
```json
{
  "status": "success",
  "path": "Contracts/Active",
  "items": [
    {
      "name": "contract_v1.pdf",
      "type": "file",
      "url": "https://...",
      "size_bytes": 15420,
      "modified": "2025-12-01T09:15:00Z",
      "modified_by": "john@company.com"
    },
    {
      "name": "VendorXYZ",
      "type": "folder",
      "url": "https://...",
      "item_count": 5
    }
  ],
  "total_items": 2
}
```

### Tool: `create_sharepoint_folder`

**Purpose**: Create new folder in SharePoint library

**Parameters**:
- `sharepoint_library` (string, required): Document library name
- `folder_path` (string, required): Full path for new folder (e.g., "Projects/Project123")
- `create_parents` (boolean, optional): Create parent folders if needed (default: true)

**Returns**:
```json
{
  "status": "success",
  "folder_url": "https://...",
  "folder_path": "Projects/Project123",
  "created_at": "2025-12-05T10:40:00Z"
}
```

### Tool: `search_sharepoint_documents`

**Purpose**: Search for documents across SharePoint site

**Parameters**:
- `query` (string, required): Search query (supports keywords, phrases)
- `libraries` (array, optional): Limit search to specific libraries
- `file_types` (array, optional): Filter by file extensions
- `modified_after` (string, optional): ISO date string for recency filter
- `max_results` (integer, optional): Limit results (default: 50)

**Returns**:
```json
{
  "status": "success",
  "query": "contractor agreement",
  "results": [
    {
      "name": "ContractorABC_Agreement.pdf",
      "url": "https://...",
      "library": "Contracts",
      "path": "Active/ContractorABC",
      "relevance_score": 0.95,
      "modified": "2025-11-15T14:30:00Z",
      "size_bytes": 18500
    }
  ],
  "total_results": 12,
  "returned_results": 12
}
```

### Tool: `get_file_metadata`

**Purpose**: Get detailed file properties and metadata

**Parameters**:
- `file_url` (string, optional): SharePoint file URL
- `file_id` (string, optional): SharePoint file unique identifier

**Returns**:
```json
{
  "status": "success",
  "name": "contract.pdf",
  "url": "https://...",
  "id": "b!abc123...",
  "size_bytes": 15420,
  "created": "2025-11-01T10:00:00Z",
  "modified": "2025-12-01T09:15:00Z",
  "created_by": "john@company.com",
  "modified_by": "jane@company.com",
  "library": "Contracts",
  "path": "Active/VendorXYZ",
  "file_type": "pdf",
  "mime_type": "application/pdf",
  "version": "1.2",
  "checkout_user": null
}
```

## Integration Requirements

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...                    # Claude API key
SHAREPOINT_SITE_URL=https://company.sharepoint.com/sites/fibreflow  # SharePoint site
SHAREPOINT_CLIENT_ID=abc123...                   # Azure AD app client ID
SHAREPOINT_CLIENT_SECRET=xyz789...               # Azure AD app secret
SHAREPOINT_TENANT_ID=tenant-id-uuid              # Azure AD tenant ID

# Optional
SHAREPOINT_DEFAULT_LIBRARY=Contracts             # Default document library
SHAREPOINT_TIMEOUT=30                            # Request timeout (seconds)
SHAREPOINT_RETRY_COUNT=3                         # Number of retries for failed requests
```

### Azure AD App Registration

To authenticate with SharePoint, you need an Azure AD app with:

**Required API Permissions**:
- `Sites.ReadWrite.All` - Read and write to all site collections
- `Files.ReadWrite.All` - Read and write files in all site collections

**Grant admin consent** for these permissions in Azure Portal.

**Authentication Flow**: OAuth2 Client Credentials flow

### External Dependencies

**Python Packages** (add to requirements.txt):
```
requests>=2.31.0
msal>=1.25.0
```

**Why needed**:
- `requests`: HTTP client for SharePoint REST API calls
- `msal`: Microsoft Authentication Library for OAuth2 token acquisition

### Network Requirements

- Outbound HTTPS access to `*.sharepoint.com`
- Outbound HTTPS access to `login.microsoftonline.com` (Azure AD)

### Orchestrator Triggers

**Keywords that should route to this agent**:
- sharepoint
- upload document
- download file
- document library
- microsoft teams files
- sharepoint site
- file storage
- document management

## Success Criteria

Agent is complete when:
- [x] All 6 tools implemented and working
- [x] OAuth2 authentication with Azure AD successful
- [x] Full test coverage (unit + integration tests with SharePoint sandbox)
- [x] README.md documentation with setup instructions
- [x] Registered in orchestrator/registry.json with triggers
- [x] Demo script can upload/download/list files
- [x] Environment variables documented in .env.example
- [x] Error handling for network failures, auth errors, permission issues
- [x] Follows BaseAgent pattern from shared/base_agent.py
- [x] Retry logic for transient failures
- [x] Progress tracking for large file uploads/downloads
- [x] Input validation for all tool parameters

## Architecture

```
User Query → Orchestrator → SharePoint Agent → Microsoft Graph API
                                 ↓
                    [OAuth2 Token Manager]
                                 ↓
                    [upload, download, list, create, search, metadata]
                                 ↓
                    SharePoint Online (Document Libraries)
```

**Position in FibreFlow**:
- **Inherits from**: `shared/base_agent.py` (BaseAgent)
- **Registers in**: `orchestrator/registry.json`
- **Tests in**: `tests/test_sharepoint.py`
- **Demo**: `demo_sharepoint.py`
- **Type**: External Integration
- **Model**: claude-3-haiku-20240307 (fast, low-cost)

## Example Usage

### Via Orchestrator

```python
# User asks to upload document
query = "Upload the contractor agreement to SharePoint in the Contracts folder"
# Orchestrator detects keywords: "upload", "sharepoint", "contracts"
# Routes to SharePointAgent
# Agent extracts file path and executes upload_file_to_sharepoint tool
```

### Direct Usage

```python
import os
from agents.sharepoint.agent import SharePointAgent

# Initialize
agent = SharePointAgent(
    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
)

# Upload file
response = agent.chat(
    "Upload /tmp/contract.pdf to the Contracts library in folder Active/VendorXYZ"
)
print(response)
# Output: "File uploaded successfully to SharePoint. URL: https://..."

# List files
response = agent.chat(
    "List all PDF files in the Contracts/Active folder"
)
print(response)
# Output: "Found 12 PDF files: contract_v1.pdf, contract_v2.pdf, ..."

# Download file
response = agent.chat(
    "Download the file at https://company.sharepoint.com/.../contract.pdf to /tmp/"
)
print(response)
# Output: "File downloaded successfully to /tmp/contract.pdf (15.4 KB)"
```

## Complexity Estimate

**Classification**: Moderate Agent

**Features**:
- 6 tools with moderate complexity
- OAuth2 authentication flow
- External API integration (Microsoft Graph)
- Error handling and retries
- File I/O operations
- Progress tracking

**Estimated Metrics**:
- **Test Cases**: 60-80 granular features
- **Build Time**: 10-14 hours (overnight run)
- **Cost**: $12-18 (using Haiku)
- **LOC**: ~500-700 lines (agent.py)

**Breakdown**:
- Scaffolding: 5 features (5%)
- Base implementation: 8 features (10%)
- Tools: 30 features (50%) - 6 tools × 5 features each
- Testing: 15 features (20%)
- Documentation: 8 features (10%)
- Integration: 4 features (5%)

## Notes

### Authentication Considerations

- **Token Caching**: Cache OAuth2 access tokens (valid for 1 hour) to avoid excessive auth requests
- **Refresh Strategy**: Implement token refresh before expiration
- **Error Recovery**: Handle `401 Unauthorized` by re-authenticating

### Performance Optimization

- **Chunked Upload**: For files >4MB, use chunked upload API
- **Parallel Downloads**: When listing+downloading multiple files, use concurrent requests
- **Request Throttling**: Respect SharePoint throttling limits (see HTTP 429 responses)

### Security Best Practices

- **Never log client secrets** in error messages or debug output
- **Validate file paths** to prevent directory traversal attacks
- **Sanitize file names** before uploading (remove special characters)
- **Check file sizes** before upload (enforce reasonable limits)

### SharePoint API Limits

- **File size**: Max 250 GB per file (use chunked upload for >100MB)
- **Request rate**: ~600 requests/minute per app (throttling applies)
- **Storage**: Depends on SharePoint plan (typically 1TB+ for enterprise)

### Testing Strategy

**Unit Tests**:
- Mock SharePoint API responses
- Test OAuth2 token acquisition
- Validate tool input/output schemas
- Test error handling paths

**Integration Tests**:
- Use SharePoint sandbox/dev site
- Test real file upload/download
- Verify folder creation
- Test search functionality
- Validate metadata retrieval

**Fixtures** (for pytest):
```python
@pytest.fixture
def sharepoint_agent():
    return SharePointAgent(os.getenv('ANTHROPIC_API_KEY'))

@pytest.fixture
def test_file():
    # Create temporary test file
    path = "/tmp/test_upload.txt"
    with open(path, 'w') as f:
        f.write("Test content")
    yield path
    os.remove(path)
```

### Common Issues and Solutions

**Issue**: `401 Unauthorized` errors
**Solution**: Verify Azure AD app has correct API permissions and admin consent granted

**Issue**: `404 Not Found` for document library
**Solution**: Check site URL and library name are correct (case-sensitive)

**Issue**: Slow uploads for large files
**Solution**: Implement chunked upload for files >10MB

**Issue**: Token expiration mid-operation
**Solution**: Implement token refresh logic with retry

### Future Enhancements

- **Version Control**: Support for SharePoint versioning (check-in/check-out)
- **Metadata Management**: Set custom metadata on uploaded files
- **Permissions Management**: Share files with specific users/groups
- **Webhook Support**: Monitor for file changes
- **Bulk Operations**: Batch upload/download multiple files efficiently
