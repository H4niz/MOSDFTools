# macOS Forensics Artifacts Analyzer (mFAA)

A digital forensics tool for macOS live acquisition and analysis of FSEvents and Extended Attributes.

## Overview

mFAA is designed for forensics investigators working with modern macOS systems (10.13+) where traditional physical acquisition is not feasible due to FileVault 2 encryption on Apple Silicon and T2 Security Chip devices.

### Key Features

- **FSEvents Analysis**: Parse and analyze file system events (v1 and v2/DLS formats)
- **Extended Attributes**: Extract and decode quarantine flags, download sources
- **Priority Scoring**: Automatic prioritization of suspicious events
- **Pattern Detection**: Identify ransomware, data exfiltration, persistence mechanisms
- **Timeline Generation**: Create chronological timelines of file system activity
- **Multiple Report Formats**: CSV, JSON, and interactive HTML reports

## Requirements

- macOS 10.13 (High Sierra) or later
- Python 3.9+
- Root/Administrator privileges (for FSEvents collection)
- APFS file system

## Installation

### From Source

```bash
# Clone repository
git clone https://github.com/yourusername/mfaa.git
cd mfaa

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Using Docker

```bash
# Build production container
docker build -f Dockerfile.prod -t mfaa:prod .

# Run analysis
docker run --privileged -v /output:/output mfaa:prod analyze
```

## Quick Start

### Full Analysis

```bash
# Run complete analysis (requires sudo)
sudo mfaa analyze --output-dir /path/to/output
```

### Collection Only

```bash
# Collect artifacts without analysis
sudo mfaa collect --volume "/Volumes/Macintosh HD" --output-dir /path/to/output
```

### Parse Collected Data

```bash
# Parse previously collected FSEvents
mfaa parse /path/to/collected/fsevents --output parsed.json
```

### Generate Reports

```bash
# Generate HTML report
mfaa report parsed.json --format html --output report.html
```

## Usage Examples

### Custom Filtering

```bash
# Use custom filter configuration
sudo mfaa analyze \
    --filter-config examples/config/filters.yaml \
    --time-range "2025-10-01" "2025-10-26" \
    --format html
```

### Focus on High-Priority Events

```bash
# Only analyze high-priority events
sudo mfaa analyze \
    --min-priority 60 \
    --format json \
    --output high_priority.json
```

## Configuration

### Filter Configuration

Create a `filters.yaml` file:

```yaml
event_types:
  - ItemRemoved
  - ItemCreated
  - ItemRenamed

paths:
  include:
    - "^/Users/.*/Downloads/"
    - "^/Applications/"
  exclude:
    - "^/System/Library/"

extensions:
  executables:
    - .app
    - .sh
    - .command

min_priority: 40
```

### Scoring Configuration

Create a `scoring.yaml` file:

```yaml
event_types:
  ItemRemoved: 10
  ItemCreated: 5
  ItemRenamed: 7

paths:
  "^/System/": 10
  "^/Applications/": 8

file_types:
  .app: 10
  .sh: 9
  .pdf: 3
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mfaa --cov-report=html

# Run specific test module
pytest tests/test_fsevents_parser.py
```

### Code Quality

```bash
# Format code
black mfaa/ tests/

# Lint
flake8 mfaa/ tests/

# Type checking
mypy mfaa/
```

## Architecture

```
mfaa/
├── collector/      # Artifact collection
├── parser/         # Binary format parsing
├── analyzer/       # Event analysis and filtering
├── timeline/       # Timeline generation
├── reporter/       # Report generation
└── utils/          # Common utilities
```

## Security Considerations

- **Non-Destructive**: All operations are read-only
- **Hash Verification**: SHA-256 checksums for all collected artifacts
- **Chain of Custody**: Timestamped audit logs
- **NIST Compliant**: Follows NIST SP 800-86 guidelines

## Contributing

Contributions are welcome! Please:

1. Follow PEP 8 style guide
2. Use type hints
3. Write tests (maintain ≥85% coverage)
4. Update documentation

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Apple FSEvents documentation
- NIST Digital Forensics guidelines
- macOS forensics community

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/mfaa/issues
- Documentation: See `docs/` directory

## Disclaimer

This tool is intended for legitimate digital forensics investigations only. Users are responsible for ensuring compliance with applicable laws and regulations.
