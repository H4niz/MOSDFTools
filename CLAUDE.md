# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


## Project Overview

**macOS Forensics Artifacts Analyzer (mFAA)** - A digital forensics tool for macOS live acquisition and analysis of FSEvents and Extended Attributes. This tool helps forensics investigators analyze file system activities on modern macOS systems (10.13+) with APFS volumes.

**Primary Use Case:** Live acquisition and analysis when physical/dead acquisition is not feasible due to FileVault 2 encryption on Apple Silicon and T2 Security Chip devices.

## Important Project Rules

### Naming Conventions
- **CRITICAL:** Do NOT use `metadata` as a variable name or function name anywhere in the codebase
- Use descriptive alternatives like `file_info`, `volume_info`, `event_data`, `properties`, etc.

### File Organization
- **Generated markdown files:** Store ALL Claude-generated markdown files in `changes_logs/` directory
- **Generated scripts:** Store ALL Claude-generated scripts in `scripts/` directory
- Keep source code in `mfaa/` directory following the modular structure

### Docker Deployment
- Use Docker for both development and production environments
- Development and production builds should be separate configurations
- Ensure proper volume mounting for artifact collection

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running the Tool
```bash
# Full analysis pipeline (requires sudo for FSEvents access)
sudo python -m mfaa.cli analyze --output-dir /output/path

# Collection only
sudo python -m mfaa.cli collect --volume "/Volumes/MacHD" --output-dir /output/path

# Parse already collected data (no sudo needed)
python -m mfaa.cli parse /path/to/fsevents --output /output/parsed.json

# Generate report from parsed data
python -m mfaa.cli report /path/to/parsed.json --format html --output report.html
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=mfaa --cov-report=html

# Run specific test module
pytest tests/test_fsevents_parser.py

# Run specific test
pytest tests/test_fsevents_parser.py::test_parse_v1_format

# Run performance benchmarks
pytest tests/performance/

# Run security tests
pytest tests/security/
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

### Docker Commands
```bash
# Build development container
docker build -f Dockerfile.dev -t mfaa:dev .

# Build production container
docker build -f Dockerfile.prod -t mfaa:prod .

# Run in development mode
docker run -it --privileged -v /output:/output mfaa:dev

# Run in production mode
docker run --privileged -v /output:/output mfaa:prod analyze
```

## Architecture Overview

### Module Structure

```
mfaa/
├── collector/          # Artifact collection from live macOS systems
│   ├── volume_scanner.py       # Detect and scan APFS volumes
│   ├── fsevents_collector.py   # Collect FSEvents databases
│   ├── xattr_collector.py      # Extract Extended Attributes
│   └── hash_calculator.py      # SHA-256 hash verification
├── parser/            # Binary format parsing
│   ├── fsevents_parser.py      # Parse FSEvents v1 and v2 (DLS/gzip)
│   ├── xattr_parser.py         # Decode xattr values
│   ├── gzip_handler.py         # Handle compressed streams
│   └── structures.py           # Binary structure definitions
├── analyzer/          # Event analysis and intelligence
│   ├── event_filter.py         # Filter events by criteria
│   ├── priority_scorer.py      # Calculate priority scores (0-100)
│   ├── pattern_detector.py     # Detect malicious patterns
│   └── correlator.py           # Correlate related events
├── timeline/          # Timeline generation
│   ├── generator.py            # Create chronological timelines
│   ├── grouper.py             # Group related events
│   └── visualizer.py          # Visualization helpers
├── reporter/          # Report generation
│   ├── csv_reporter.py         # CSV export
│   ├── json_reporter.py        # JSON export
│   ├── html_reporter.py        # Interactive HTML reports
│   └── templates/             # Jinja2 templates
└── utils/            # Utilities
    ├── logger.py              # Logging configuration
    ├── config.py              # Configuration management
    ├── validator.py           # Input validation
    └── exceptions.py          # Custom exceptions
```

### Data Flow Pipeline

1. **Collection Phase:** `VolumeScanner` → `FSEventsCollector` + `XattrCollector` → Raw artifacts with SHA-256 hashes
2. **Parsing Phase:** `FSEventsParser` + `XattrParser` → Structured `FSEvent` and `XattrRecord` objects
3. **Analysis Phase:** `EventFilter` → `PriorityScorer` → `PatternDetector` → Filtered and scored events
4. **Timeline Phase:** `TimelineGenerator` → Chronological timeline with grouped events
5. **Reporting Phase:** `Reporter` classes → CSV/JSON/HTML reports

### Key Data Models

All data models use Python `dataclasses` and are defined with type hints:

- **VolumeInfo:** APFS volume information (name, mount point, encryption status)
- **FSEvent:** Single FSEvents record (event_id, timestamp, path, flags, node_id)
- **EventFlags:** Bitfield enum for FSEvents flags (ITEM_CREATED, ITEM_REMOVED, etc.)
- **XattrRecord:** Extended attributes for a file (quarantine info, download URLs)
- **QuarantineInfo:** Decoded `com.apple.quarantine` attribute
- **TimelineEntry:** Event + priority score + xattr + notes
- **Pattern:** Detected suspicious pattern (mass deletion, ransomware, exfiltration)

### Tool Function Mechanisms

#### FSEvents Parser
- **Auto-detection:** Automatically detects FSEvents format version (v1 or v2/DLS)
- **Version 1:** Uncompressed binary format, direct parsing
- **Version 2 (DLS):** Gzip-compressed streams, requires decompression before parsing
- **Flag Decoding:** Converts binary flags to meaningful event types using bitfield operations
- **Unicode Handling:** Properly handles Unicode paths in file system events

#### Extended Attributes Parser
- **Quarantine Parsing:** Decodes `com.apple.quarantine` hex format: `FLAGS;TIMESTAMP;APP;UUID`
- **Download Sources:** Extracts URLs from `com.apple.metadata:kMDItemWhereFroms` (binary plist format)
- **Timestamp Conversion:** Converts macOS HFS+ timestamps to datetime objects

#### Priority Scoring Algorithm
Calculates score (0-100) based on weighted factors:
- Event type weight: Removed=10, Created=5, Modified=3
- Path sensitivity: System paths=10, Applications=8, User dirs=5
- File type risk: Executables=10, Scripts=8, Documents=3
- Quarantine flag present: +5 bonus
- Downloaded from internet: +5 bonus
- Categories: CRITICAL (80-100), HIGH (60-79), MEDIUM (40-59), LOW (0-39)

#### Pattern Detection
Implements detection algorithms for:
- **Mass Deletion:** Threshold-based (>50 files in <60 seconds)
- **Ransomware:** File renames to `.encrypted`/`.locked`, ransom note creation
- **Data Exfiltration:** Large files copied to external volumes, archive creation patterns
- **Persistence Mechanisms:** LaunchAgents/LaunchDaemons creation, shell profile modifications

#### Event Filtering
- **By Type:** Filter specific FSEvents flags (ITEM_REMOVED, ITEM_CREATED, etc.)
- **By Path:** Regex pattern matching on file paths
- **By Extension:** File extension filtering (`.app`, `.sh`, `.dmg`, etc.)
- **By Time Range:** Filter events within datetime range
- **Configurable:** All filters defined in YAML configuration files

## Performance Requirements

- **Parsing Speed:** ≥ 10,000 events/second
- **Memory Usage:** ≤ 500MB for 1M events
- **Report Generation:** ≤ 5 seconds for 100K events
- **Test Coverage:** ≥ 85%

## Security & Forensics Considerations

### Forensics Best Practices
- **Non-Destructive:** All operations are read-only, no modification of source data
- **Hash Verification:** SHA-256 checksums for all collected artifacts
- **Chain of Custody:** Timestamped audit logs for all operations
- **NIST Compliance:** Follows NIST SP 800-86 guidelines for digital forensics

### Privileges
- **Root Required:** FSEvents collection requires administrator/root privileges
- **Permission Checks:** Validate permissions upfront with clear error messages
- **Graceful Degradation:** Handle permission errors without crashing

### Data Privacy
- **Local Processing:** No cloud uploads unless explicitly configured
- **PII Redaction:** Configurable redaction options for sensitive data
- **Secure Storage:** Artifacts stored with appropriate file permissions

## Configuration Files

### Filter Configuration (`filters.yaml`)
Define event filtering rules:
- `event_types`: List of FSEvents types to include
- `paths.include`: Regex patterns for paths to include
- `paths.exclude`: Regex patterns for paths to exclude
- `extensions`: File extensions grouped by category
- `time_range`: Start and end datetime filters
- `min_priority`: Minimum priority score threshold

### Scoring Configuration (`scoring.yaml`)
Define priority scoring weights:
- `event_types`: Weight for each event type (0-10)
- `paths`: Weight for path patterns (0-10)
- `file_types`: Weight for file extensions (0-10)
- `bonuses`: Bonus points for specific attributes
- `categories`: Priority level thresholds

## Common Development Patterns

### Adding a New Event Filter
1. Add filter method to `analyzer/event_filter.py`
2. Update `FilterConfig` dataclass with new parameters
3. Add configuration to `filters.yaml` schema
4. Write unit tests in `tests/test_analyzer.py`
5. Update documentation

### Adding a New Pattern Detector
1. Create detection method in `analyzer/pattern_detector.py`
2. Define pattern signature and thresholds
3. Return `Pattern` dataclass with detection results
4. Add tests with simulated malicious activity
5. Document detection logic and indicators

### Adding a New Report Format
1. Create new reporter class inheriting from `BaseReporter`
2. Implement `generate()` method
3. Add format option to CLI arguments
4. Write integration tests
5. Add example report to `examples/reports/`

## Testing Strategy

### Test Organization
- **Unit Tests (60%):** Individual module/function testing
- **Integration Tests (30%):** Multi-module pipeline testing
- **E2E Tests (10%):** Full scenario testing (ransomware, insider threat, etc.)

### Test Data
Located in `tests/fixtures/`:
- `fsevents/`: Sample FSEvents databases (v1, v2, corrupted)
- `xattr/`: Files with various Extended Attributes
- `scenarios/`: Simulated forensics scenarios

### Performance Testing
Run benchmarks with large datasets to verify:
- Parsing speed meets ≥10,000 events/sec requirement
- Memory usage stays ≤500MB for 1M events
- No memory leaks during long-running operations

## Development Timeline

**4-Week Sprint Plan:**
- Week 1: Foundation (FSEvents parser v1, project setup)
- Week 2: Core functionality (collector, parser v2, xattr extraction)
- Week 3: Analysis engine (filtering, scoring, pattern detection, timeline)
- Week 4: Reporting & finalization (CSV/JSON/HTML reporters, documentation)

## Troubleshooting

### Common Issues
- **Permission Denied:** Ensure running with `sudo` for FSEvents access
- **Parsing Errors:** Verify FSEvents format version compatibility
- **Performance Issues:** Use streaming parsing for very large datasets (>10M events)
- **False Positives:** Adjust scoring weights and pattern thresholds in config files

### Debug Mode
```bash
# Enable verbose logging
python -m mfaa.cli analyze --verbose --output-dir /output
```

## Contributing Guidelines

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Document all public APIs with docstrings
- Write tests for new features (maintain ≥85% coverage)
- Update CHANGELOG.md for significant changes
