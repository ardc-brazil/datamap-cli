# DataMap CLI

A cross-platform Python-based command-line interface for interacting with the DataMap platform API.

## Features

- **Dataset Management**: Retrieve dataset information and list versions
- **File Operations**: List files in specific versions and download them
- **Download Capabilities**: Download single files or entire versions with progress tracking
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Rich Output**: Beautiful terminal output with progress bars and formatting
- **Configuration Management**: Flexible configuration via environment variables or config files
- **Comprehensive Help System**: Topic-specific help with examples, troubleshooting, and guides
- **Multiple Output Formats**: Support for table, JSON, YAML, and CSV output
- **Global Options**: Consistent options across all commands
- **Interactive Features**: Progress tracking, confirmations, and user prompts
- **Scripting Support**: Quiet mode and structured output for automation

## Installation

### Prerequisites

- Python 3.8 or higher
- Poetry (recommended) or pip

### Using Poetry (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd datamap-cli
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

4. **Run the CLI:**
   ```bash
   poetry run datamap --help
   ```

### Using pip

1. **Install from PyPI (when available):**
   ```bash
   pip install datamap-cli
   ```

2. **Set up environment variables:**
   ```bash
   export DATAMAP_API_KEY="your-api-key"
   export DATAMAP_API_SECRET="your-api-secret"
   ```

3. **Run the CLI:**
   ```bash
   datamap --help
   ```

## Configuration

### Environment Variables

The following environment variables can be configured:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATAMAP_API_KEY` | Your DataMap API key | Required |
| `DATAMAP_API_SECRET` | Your DataMap API secret | Required |
| `DATAMAP_API_BASE_URL` | API base URL | `https://datamap.pcs.usp.br/api/v1` |
| `DATAMAP_TIMEOUT` | Request timeout (seconds) | `30` |
| `DATAMAP_RETRY_ATTEMPTS` | Retry attempts for failed requests | `3` |
| `DATAMAP_LOG_LEVEL` | Logging level | `INFO` |
| `DATAMAP_OUTPUT_FORMAT` | Output format (table/json/yaml/csv) | `table` |
| `DATAMAP_COLOR_OUTPUT` | Enable colored output | `true` |

### Configuration File

You can also use a `.env` file in your project directory:

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual values
nano .env
```

### Configuration Validation

Validate your configuration to ensure everything is set up correctly:

```bash
# Validate configuration
datamap --validate-config

# Show current configuration
datamap config show

# Initialize a new configuration file
datamap config init --config-file ~/.datamap/config.yaml
```

## Usage

### Basic Commands

```bash
# Show help
datamap --help

# Show version
datamap --version

# Enable verbose output
datamap --verbose <command>

# Suppress output (useful for scripting)
datamap --quiet <command>

# Validate configuration
datamap --validate-config
```

### Help System

The CLI provides comprehensive help with topic-specific guidance:

```bash
# Show command examples
datamap --help-topic examples

# Show troubleshooting guide
datamap --help-topic troubleshooting

# Show output format guide
datamap --help-topic formats

# Show configuration guide
datamap --help-topic config

# Show scripting guide
datamap --help-topic scripting
```

### Dataset Commands

```bash
# Get dataset information
datamap dataset info <dataset-uuid>

# List dataset versions
datamap dataset versions <dataset-uuid>
```

### Version Commands

```bash
# List files in a version
datamap version files <dataset-uuid> <version-name>
```

### Download Commands

```bash
# Download a single file
datamap download file <dataset-uuid> <version-name> <file-uuid>

# Download all files in a version
datamap download version <dataset-uuid> <version-name>

# Download to specific directory
datamap download version <dataset-uuid> <version-name> --output-dir ./downloads

# Resume interrupted download
datamap download file <dataset-uuid> <version-name> <file-uuid> --resume

# Download with progress tracking (default)
datamap download version <dataset-uuid> <version-name>

# Download in quiet mode (for scripting)
datamap --quiet download version <dataset-uuid> <version-name>
```

### Output Formats

The CLI supports multiple output formats for different use cases:

```bash
# Rich tables (default) - Best for interactive use
datamap dataset info <uuid> --output-format table

# JSON output - Best for scripting and API integration
datamap dataset info <uuid> --output-format json

# YAML output - Best for configuration files
datamap dataset info <uuid> --output-format yaml

# CSV output - Best for spreadsheet import
datamap dataset info <uuid> --output-format csv

# Global output format (applies to all commands)
datamap --output-format json dataset info <uuid>
```

### Global Options

The CLI supports global options that apply to all commands:

```bash
# Output control
--output-format, -f    Choose output format (table/json/yaml/csv)
--color/--no-color     Enable/disable colored output
--verbose, -V          Enable detailed logging
--quiet, -q            Suppress normal output, show only errors

# Configuration
--config, -c           Specify configuration file
--validate-config      Validate configuration and exit
```

### Enhanced User Experience

The CLI provides a rich, interactive experience:

- **Progress Tracking**: Visual progress bars for downloads and operations
- **Interactive Confirmations**: Prompts for destructive operations and large downloads
- **Rich Formatting**: Beautiful tables, panels, and colorized output
- **Smart Defaults**: Sensible defaults with easy customization
- **Error Handling**: Clear error messages with actionable suggestions
- **Command Completion**: Tab completion for commands and options (when available)

## Development

### Setting up Development Environment

1. **Clone and install:**
   ```bash
   git clone <repository-url>
   cd datamap-cli
   poetry install
   ```

2. **Install pre-commit hooks:**
   ```bash
   poetry run pre-commit install
   ```

3. **Run tests:**
   ```bash
   poetry run pytest
   ```

### Code Quality

The project uses several tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

Run all quality checks:

```bash
poetry run black src tests
poetry run isort src tests
poetry run flake8 src tests
poetry run mypy src
poetry run pytest
```

### Project Structure

```
datamap-cli/
├── src/datamap_cli/          # Main package
│   ├── cli.py               # CLI entry point
│   ├── commands/            # Command implementations
│   ├── api/                 # API client layer
│   ├── config/              # Configuration management
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── docs/                    # Documentation
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- **Built-in Help**: Use `datamap --help-topic troubleshooting` for common issues
- **Configuration Help**: Use `datamap config help` for configuration guidance
- **Examples**: Use `datamap --help-topic examples` for usage examples
- **Documentation**: Check the documentation in the `docs/` directory
- **GitHub Issues**: Open an issue on GitHub
- **Contact**: Contact the development team

### Quick Troubleshooting

```bash
# Check if configuration is valid
datamap --validate-config

# Enable verbose logging for debugging
datamap --verbose <command>

# Get help for specific topics
datamap --help-topic troubleshooting
datamap --help-topic config
```

## Roadmap

- [x] **CLI Framework and User Experience** - Comprehensive help system, global options, rich formatting
- [x] **Core API Client** - Authentication, request handling, error management
- [x] **Configuration Management** - Environment variables, config files, validation
- [x] **Download System** - File downloads with progress tracking and resume capability
- [x] **Dataset and Version Commands** - Information retrieval and listing
- [ ] Interactive mode with TUI
- [ ] Batch operations support
- [ ] Plugin system
- [ ] Advanced caching
- [ ] Export to additional formats
