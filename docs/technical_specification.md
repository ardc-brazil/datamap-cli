# DataMap CLI – Technical Specification

## Overview

This document outlines the technical implementation details for the DataMap CLI tool, a cross-platform Python-based command-line interface for interacting with the DataMap platform API.

## Architecture Overview

### Technology Stack

- **Language:** Python 3.8+
- **CLI Framework:** Typer
- **HTTP Client:** httpx (async-capable, modern HTTP library)
- **Configuration:** Pydantic (data validation and settings management)
- **Logging:** structlog (structured logging)
- **Testing:** pytest (testing framework)
- **Build System:** Poetry (dependency management and packaging)

### Project Structure

```
datamap-cli/
├── src/
│   └── datamap_cli/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── commands/           # Command implementations
│       │   ├── __init__.py
│       │   ├── dataset.py      # Dataset-related commands
│       │   ├── version.py      # Version-related commands
│       │   ├── file.py         # File-related commands
│       │   └── download.py     # Download functionality
│       ├── api/                # API client layer
│       │   ├── __init__.py
│       │   ├── client.py       # Main API client
│       │   ├── models.py       # Pydantic models for API responses
│       │   └── exceptions.py   # Custom API exceptions
│       ├── config/             # Configuration management
│       │   ├── __init__.py
│       │   └── settings.py     # Application settings
│       ├── utils/              # Utility functions
│       │   ├── __init__.py
│       │   ├── logging.py      # Logging configuration
│       │   └── progress.py     # Progress indicators
│       └── exceptions.py       # Application exceptions
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_api/
│   └── test_commands/
├── docs/                       # Documentation
├── pyproject.toml             # Project configuration
├── README.md
└── .env.example               # Environment variables template
```

## Core Components

### 1. CLI Layer (`cli.py`)

**Responsibilities:**
- Main entry point for the application
- Command group organization
- Global options and configuration
- Error handling and user feedback

**Key Features:**
- Uses Click for command-line interface
- Supports global options (--verbose, --config, --output-format)
- Implements consistent error handling
- Provides help and version information

### 2. API Client (`api/client.py`)

**Responsibilities:**
- HTTP communication with DataMap API
- Authentication handling
- Request/response processing
- Rate limiting and retry logic

**Key Features:**
- Async-capable HTTP client using httpx
- Automatic authentication header injection
- Response validation using Pydantic models
- Configurable retry logic with exponential backoff
- Request/response logging for debugging

### 3. Data Models (`api/models.py`)

**Responsibilities:**
- Define data structures for API requests/responses
- Provide validation and serialization
- Ensure type safety throughout the application

**Key Models:**
```python
class Dataset(BaseModel):
    id: str  # UUID
    name: str
    data: dict  # Dataset information in JSON format
    tenancy: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    design_state: str
    versions: List[Version] = []
    current_version: Optional[Version]

class Version(BaseModel):
    id: str  # UUID
    name: str  # Version name (string, not UUID)
    design_state: str
    is_enabled: bool
    files: List[DataFile] = []
    created_at: datetime
    updated_at: datetime

class DataFile(BaseModel):
    id: str  # UUID
    name: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    extension: Optional[str]
    format: Optional[str]
    storage_file_name: Optional[str]
    storage_path: Optional[str]
    created_by: Optional[str]  # UUID

class DataFileDownloadResponse(BaseModel):
    url: str  # Download URL
```

### 4. Configuration Management (`config/settings.py`)

**Responsibilities:**
- Application settings management
- Environment variable handling
- Configuration validation
- Default value management

**Configuration Sources (in order of precedence):**
1. Command-line arguments
2. Environment variables
3. Configuration file
4. Default values

**Key Settings:**
- `DATAMAP_API_KEY`: Application API key for authentication
- `DATAMAP_API_SECRET`: Application API secret for authentication
- `DATAMAP_API_BASE_URL`: API base URL (default: https://datamap.pcs.usp.br/api/v1)
- `DATAMAP_TIMEOUT`: Request timeout in seconds
- `DATAMAP_RETRY_ATTEMPTS`: Number of retry attempts for failed requests

## Command Implementation

### 1. Dataset Commands

#### `datamap dataset info <uuid>`
- **Purpose:** Retrieve and display dataset metadata
- **Implementation:** Single API call to `/datasets/{uuid}`
- **Output:** Formatted display of dataset information
- **Error Handling:** Invalid UUID, dataset not found, API errors

#### `datamap dataset versions <uuid>`
- **Purpose:** List all versions of a dataset
- **Implementation:** API call to `/v1/datasets/{id}` (versions are included in the response)
- **Output:** Tabular display of versions with names and metadata
- **Error Handling:** Invalid UUID, dataset not found, API errors

### 2. Version Commands

#### `datamap version files <dataset_uuid> <version_name>`
- **Purpose:** List all files in a specific version
- **Implementation:** API call to `/v1/datasets/{dataset_id}/versions/{version_name}` (files are included in the response)
- **Output:** Tabular display of files with metadata
- **Error Handling:** Invalid UUID, version not found, API errors

### 3. Download Commands
#### `datamap download file <dataset_uuid> <version_name> <file_uuid> [--output-dir PATH]`
- **Purpose:** Download a single file by UUID
- **Implementation:**
  - Get download URL from `/v1/datasets/{dataset_id}/versions/{version_name}/files/{file_id}`
  - Download from the returned URL
  - Save to specified output directory or current directory
- **Features:**
  - Progress bar for download
  - Resume capability for interrupted download
  - Checksum verification (if available)
- **Error Handling:** Network errors, disk space issues, permission errors

#### `datamap download version <dataset_uuid> <version_name> [--output-dir PATH]`
- **Purpose:** Download all files from a version
- **Implementation:** 
  - Fetch version details from `/v1/datasets/{dataset_id}/versions/{version_name}` (includes files array)
  - For each file, get download URL from `/v1/datasets/{dataset_id}/versions/{version_name}/files/{file_id}`
  - Download each file with progress indication
  - Preserve directory structure if specified
- **Features:**
  - Progress bars for individual files and overall progress
  - Resume capability for interrupted downloads
  - Checksum verification (if available)
  - Concurrent downloads (configurable)
- **Error Handling:** Network errors, disk space issues, permission errors

## API Integration

### Base URL
- **Production:** `https://datamap.pcs.usp.br/api/v1`
- **Development:** Configurable via environment variable

### Authentication
- **Method:** API Key and Secret authentication
- **Headers:** 
  - `X-Api-Key`: Application API key
  - `X-Api-Secret`: Application API secret
  - `X-User-Id`: User ID (optional)
  - `X-Datamap-Tenancies`: Tenancy information (optional)
- **Storage:** Environment variables or configuration file

### Endpoints

Based on the API documentation at https://datamap.pcs.usp.br/api/docs, the following endpoints will be used:

1. **GET /v1/datasets/{id}** - Retrieve dataset metadata (includes versions array)
2. **GET /v1/datasets/{dataset_id}/versions/{version_name}** - Get specific version details (includes files array)
3. **GET /v1/datasets/{dataset_id}/versions/{version_name}/files/{file_id}** - Get file download URL

### Error Handling

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid UUID format)
- `401`: Unauthorized (invalid credentials)
- `404`: Not Found (dataset/version/file doesn't exist)
- `429`: Rate Limited
- `500`: Server Error

**Application Errors:**
- Invalid UUID format
- Network connectivity issues
- Authentication failures
- File system errors during downloads

## User Experience

### Output Formats

**Default Format:** Human-readable, colorized output
**Alternative Formats:**
- `--json`: JSON output for scripting
- `--yaml`: YAML output for configuration
- `--csv`: CSV output for data processing

### Progress Indicators

**Download Progress:**
- Overall progress bar
- Individual file progress
- Transfer speed and ETA
- File size and completion percentage

**Command Progress:**
- Spinner for API calls
- Progress indicators for long-running operations

### Error Messages

**User-Friendly Messages:**
- Clear, actionable error descriptions
- Suggested solutions when possible
- Reference to documentation or help

**Debug Information:**
- Verbose mode for detailed error information
- Request/response logging
- Stack traces for unexpected errors

## Security Considerations

### Credential Management

**Environment Variables:**
```bash
export DATAMAP_API_KEY="your-api-key"
export DATAMAP_API_SECRET="your-api-secret"
```

**Configuration File:**
```ini
[datamap]
api_key = your-api-key
api_secret = your-api-secret
```

**Security Measures:**
- Credentials never logged or displayed
- Configuration file permissions restricted
- Secure credential storage recommendations

### Input Validation

**UUID Validation:**
- Strict UUID format validation
- Prevention of path traversal attacks
- Sanitization of user inputs

**File System Security:**
- Safe file path handling
- Prevention of directory traversal
- Proper file permissions

## Performance Considerations

### Optimization Strategies

**API Calls:**
- Connection pooling
- Request caching for metadata
- Parallel requests where appropriate

**Downloads:**
- Chunked downloads for large files
- Concurrent downloads (configurable)
- Resume capability for interrupted downloads

**Memory Management:**
- Streaming downloads for large files
- Efficient data structures
- Proper resource cleanup

### Scalability

**Large Datasets:**
- Pagination support for large result sets
- Streaming processing for large files
- Memory-efficient operations

**Concurrent Operations:**
- Configurable concurrency limits
- Rate limiting compliance
- Resource management

## Testing Strategy

### Test Categories

**Unit Tests:**
- Individual function testing
- Mock API responses
- Error condition testing

**Integration Tests:**
- API client testing
- End-to-end command testing
- Configuration testing

**End-to-End Tests:**
- Complete workflow testing
- Cross-platform compatibility
- Performance testing

### Test Coverage

**Target Coverage:** 90%+
**Critical Areas:**
- API client functionality
- Command implementations
- Error handling
- Configuration management

## Deployment and Distribution

### Packaging

**Tool:** Poetry for dependency management and packaging
**Format:** Wheel distribution
**Platforms:** Windows, macOS, Linux

### Installation Methods

**PyPI:**
```bash
pip install datamap-cli
```

**Development:**
```bash
git clone <repository>
cd datamap-cli
poetry install
poetry run datamap --help
```

### Distribution

**Release Process:**
1. Version bump and changelog update
2. Automated testing
3. Build and package creation
4. PyPI publication
5. GitHub release creation

## Development Workflow

### Code Quality

**Linting:** flake8, black, isort
**Type Checking:** mypy
**Pre-commit Hooks:** Automated code quality checks

### Documentation

**Code Documentation:** Google-style docstrings
**API Documentation:** OpenAPI/Swagger integration
**User Documentation:** Comprehensive README and help system

### Version Control

**Branch Strategy:** GitFlow or GitHub Flow
**Commit Messages:** Conventional Commits format
**Release Tags:** Semantic versioning

## Future Enhancements

### Potential Features

1. **Interactive Mode:** TUI for browsing datasets
2. **Batch Operations:** Process multiple datasets
3. **Data Validation:** Verify downloaded file integrity
4. **Plugin System:** Extensible command architecture
5. **Export Formats:** Additional output formats
6. **Caching:** Local metadata caching
7. **Notifications:** Download completion notifications

### Scalability Considerations

1. **API Versioning:** Support for future API versions
2. **Plugin Architecture:** Extensible command system
3. **Configuration Evolution:** Backward-compatible settings
4. **Performance Monitoring:** Built-in performance metrics

## Conclusion

This technical specification provides a comprehensive foundation for implementing the DataMap CLI tool. The architecture prioritizes maintainability, user experience, and cross-platform compatibility while following modern Python development practices.

The implementation will be iterative, starting with core functionality and expanding based on user feedback and requirements evolution. 