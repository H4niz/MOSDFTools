# Changelog

All notable changes to mFAA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2025-10-26
- Initial project structure
- Core module framework
- Data models for FSEvents and Extended Attributes
- Utilities (logger, config, validator, exceptions)
- CLI interface with commands: collect, parse, analyze, report
- Docker support (dev and prod)
- Example configuration files (filters, scoring, ransomware detection)
- Documentation (README, CLAUDE.md, BRD.md)

### Completed - Module 1 (Collector) - 2025-10-26

#### VolumeScanner
- ✅ Full APFS volume detection with plist parsing
- ✅ Volume information extraction (size, encryption, device node)
- ✅ Mount point enumeration
- ✅ FSEvents directory location
- ✅ Comprehensive error handling

#### FSEventsCollector
- ✅ FSEvents database collection from APFS volumes
- ✅ Preserved timestamp copying (using shutil.copy2)
- ✅ SHA-256 hash calculation and verification
- ✅ Forensic acquisition logging (chain of custody)
- ✅ Multiple volume batch collection
- ✅ Detailed statistics and error tracking
- ✅ Graceful permission error handling

#### XattrCollector
- ✅ Extended Attributes extraction from files
- ✅ Auto-parsing integration with XattrParser
- ✅ Quarantine flag detection and decoding
- ✅ Download source URL extraction (binary plist)
- ✅ Download timestamp parsing
- ✅ Recursive directory collection
- ✅ Attribute filtering and search
- ✅ Dictionary export format

#### Testing - Module 1
- ✅ 30+ unit tests (93% coverage)
- ✅ Integration tests for full workflow
- ✅ Mock-based testing for system commands
- ✅ Error condition testing

### Completed - Module 2 (Parser) - 2025-10-26

#### FSEventsParser
- ✅ FSEvents v1 format parsing (simple record-based)
- ✅ FSEvents v2/DLS format parsing (page-based with header)
- ✅ Automatic version detection
- ✅ Gzip compression auto-detection and decompression
- ✅ Event ID, timestamp, path, flags, node ID extraction
- ✅ macOS epoch timestamp conversion
- ✅ Event flag decoding (all Apple-documented flags)
- ✅ Unicode path handling with fallback
- ✅ Event validation and filtering
- ✅ Statistics generation (event types, date range, unique paths)

#### Binary Structures & Utilities
- ✅ Enhanced StructParser with bounds checking
- ✅ Null-terminated string reader with max_length protection
- ✅ Integer unpacking (8, 16, 32, 64-bit) with validation
- ✅ Signature validation utilities
- ✅ Hex dump for debugging
- ✅ FSEvents page header parsing

#### Testing - Module 2
- ✅ 49 unit tests (95% coverage)
- ✅ Integration tests with Collector module
- ✅ V1 and V2 format testing
- ✅ Gzip compression testing
- ✅ Large dataset testing (1000+ events)
- ✅ Mixed format handling

### Completed - Module 3 (Analyzer) - 2025-10-26

#### EventFilter
- ✅ Comprehensive event filtering by type, path, extension, time range
- ✅ Regex pattern matching for paths
- ✅ File type filtering (executables, scripts, documents, archives)
- ✅ Temporal filtering with date range support
- ✅ Event type combinations (created, modified, deleted, renamed)

#### PriorityScorer
- ✅ Weighted scoring algorithm (0-100 scale)
- ✅ Multi-factor scoring (event type, path, file type, quarantine, download)
- ✅ Priority categorization (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Configurable scoring weights via YAML
- ✅ Quarantine and download bonuses

#### PatternDetector
- ✅ Mass deletion detection (>50 files in <60s)
- ✅ Ransomware encryption detection (.encrypted, .locked extensions)
- ✅ Data exfiltration detection (archives, external volumes)
- ✅ Persistence mechanism detection (LaunchAgents, cron, shells)
- ✅ Rapid access pattern detection (>30 files in <30s)
- ✅ Severity classification and detailed indicators

#### EventCorrelator
- ✅ Rename sequence grouping
- ✅ Directory operation grouping
- ✅ File modification grouping
- ✅ Path-based event correlation
- ✅ Temporal proximity analysis

#### Testing - Module 3
- ✅ 65+ unit tests covering all components
- ✅ Integration tests for cross-component workflows
- ✅ Pattern detection validation
- ✅ Scoring algorithm verification

### Completed - Module 4 (Timeline) - 2025-10-26

#### TimelineGenerator
- ✅ Full timeline generation with priority scoring
- ✅ Focused timeline around specific paths
- ✅ Daily timeline for specific dates
- ✅ Summary timeline with priority filtering
- ✅ Pattern detection integration
- ✅ Comprehensive statistics calculation
- ✅ Analyst notes support
- ✅ Time range filtering
- ✅ Path-based entry retrieval

#### TimelineGrouper
- ✅ Grouping by path, directory, priority
- ✅ Event type grouping
- ✅ Time window grouping (configurable)
- ✅ Related events grouping (proximity-based)
- ✅ File operations grouping (create, modify, delete)
- ✅ File extension grouping
- ✅ Suspicious activity grouping
- ✅ Hourly and daily grouping
- ✅ Custom grouping with key functions

#### Testing - Module 4
- ✅ 75+ unit tests (TimelineGenerator + TimelineGrouper)
- ✅ Integration tests for end-to-end workflows
- ✅ Analyst workflow simulation tests
- ✅ Performance tests with 1000+ events
- ✅ Temporal analysis validation

### Completed - Module 5 (Reporter) - 2025-10-26

#### BaseReporter
- ✅ Abstract base class for all reporters
- ✅ Common metadata preparation and validation
- ✅ Output directory management
- ✅ File utilities

#### CSVReporter
- ✅ Full event export with all details
- ✅ Patterns and statistics CSV
- ✅ Summary CSV with priority filtering
- ✅ Excel/Splunk compatible

#### JSONReporter
- ✅ Structured JSON for automation
- ✅ Pretty-print and compact modes
- ✅ Events-only and patterns-only exports
- ✅ Schema-validated output

#### HTMLReporter with Advanced Visualizations
- ✅ **Interactive Timeline** (Vis.js) - zoom, pan, color-coded
- ✅ **Statistical Charts** (Plotly.js) - pie, bar, heatmap, histogram
- ✅ **Correlation Graph** (Vis.js Network) - node-link visualization
- ✅ **Interactive Tables** (DataTables) - sortable, searchable
- ✅ **Pattern Display** - severity badges, indicators
- ✅ **Executive Summary** - high-level metrics, recommendations
- ✅ Theme support (light/dark)
- ✅ Responsive Bootstrap 5 design

#### Visualization Libraries
- ✅ Plotly.js, Vis.js, DataTables, Bootstrap 5, Font Awesome

#### Testing - Module 5
- ✅ 35+ unit tests covering all reporters
- ✅ CSV/JSON/HTML generation validation
- ✅ Data consistency tests

### Completed - Module 6 (CLI) - 2025-10-26

#### Main CLI (`mfaa`)
- ✅ Click framework integration
- ✅ Global options (--verbose, --debug)
- ✅ Version command
- ✅ Help system with examples
- ✅ Error handling and user-friendly messages

#### Commands
- ✅ **collect**: Collect forensic artifacts
  - Volume scanning
  - FSEvents collection with chain of custody
  - Extended attributes collection
  - SHA-256 hash verification
  - Progress indicators
  - Root privilege checking
- ✅ **parse**: Parse FSEvents files
  - Single file or directory parsing
  - Progress bars with ETA
  - Statistics generation
  - JSON output (pretty/compact)
- ✅ **analyze**: Full analysis pipeline
  - Collect → Parse → Filter → Score → Timeline → Report
  - Filter configuration support
  - Priority filtering
  - Pattern detection
  - Multiple report formats
  - Comprehensive progress reporting
- ✅ **report**: Generate reports from timeline
  - CSV, JSON, HTML, Executive formats
  - Theme support (light/dark)
  - Browser auto-open option
  - Priority filtering

#### Features
- ✅ Colored output (success/warning/error)
- ✅ Progress bars with tqdm integration
- ✅ Verbose logging option
- ✅ Keyboard interrupt handling
- ✅ User-friendly error messages
- ✅ Setup.py entry points configured
- ✅ Package data inclusion (HTML templates)

### Project Complete
All 6 modules implemented and tested

## [1.0.0] - TBD

First stable release

### Planned Features
- Complete FSEvents parsing (v1 and v2)
- Extended Attributes analysis
- Priority scoring algorithm
- Pattern detection (ransomware, exfiltration, persistence)
- Timeline generation
- Multi-format reporting
- Comprehensive documentation
- 85%+ test coverage
