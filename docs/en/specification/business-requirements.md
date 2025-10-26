# Tài Liệu Đặc Tả Sản Phẩm
## macOS Live Acquisition & Artifacts Analysis Tool

**Phiên bản:** 1.0  
**Ngày:** 26/10/2025  
**Trạng thái:** Draft - Để Phê Duyệt  
**Thời gian phát triển:** 4 tuần

---

## 📋 Mục Lục

1. [Tổng Quan Dự Án](#1-tổng-quan-dự-án)
2. [Phân Tích Nghiệp Vụ](#2-phân-tích-nghiệp-vụ)
3. [Yêu Cầu Chức Năng](#3-yêu-cầu-chức-năng)
4. [Kiến Trúc Hệ Thống](#4-kiến-trúc-hệ-thống)
5. [Đặc Tả API](#5-đặc-tả-api)
6. [Data Models](#6-data-models)
7. [Lộ Trình Phát Triển](#7-lộ-trình-phát-triển)
8. [Test Strategy](#8-test-strategy)
9. [Security & Compliance](#9-security--compliance)
10. [Deliverables](#10-deliverables)

---

## 1. Tổng Quan Dự Án

### 1.1 Executive Summary

**Tên Dự Án:** macOS Forensics Artifacts Analyzer (mFAA)

**Vấn Đề:** Các thiết bị macOS hiện đại với chip Apple Silicon (M1/M2/M3) và T2 Security Chip sử dụng mã hóa phần cứng FileVault 2, khiến việc thu thập dữ liệu vật lý (physical/dead acquisition) không khả thi khi không có thông tin xác thực. Live acquisition trở thành phương pháp duy nhất, nhưng việc phân tích thủ công các artifacts như FSEvents và Extended Attributes mất nhiều thời gian và dễ bỏ sót bằng chứng quan trọng.

**Giải Pháp:** Xây dựng công cụ tự động hóa thu thập, phân tích và lọc FSEvents/xattr với khả năng:
- Trích xuất và giải mã FSEvents từ APFS volumes
- Phân tích Extended Attributes (quarantine flags, download sources)
- Tạo priority timeline cho các hoạt động đáng ngờ
- Xuất báo cáo dưới nhiều định dạng (CSV, JSON, HTML)

**Đối Tượng Người Dùng:**
- Digital Forensics Investigators
- Incident Response Teams
- Security Analysts
- Law Enforcement Agencies

### 1.2 Goals & Success Metrics

**Primary Goals:**
1. Thu thập và parse được 100% FSEvents từ macOS 10.13+ đến macOS 15+
2. Trích xuất và phân loại Extended Attributes (xattr)
3. Giảm 80% thời gian phân tích thủ công
4. Tạo timeline với độ chính xác timestamp < 1 giây

**Success Metrics:**
- Parsing accuracy: ≥ 99.5%
- Processing speed: ≥ 10,000 events/second
- False positive rate: ≤ 5%
- Code coverage: ≥ 85%
- Documentation completeness: 100%

### 1.3 Constraints & Assumptions

**Constraints:**
- Thời gian phát triển: 4 tuần
- Ngôn ngữ: Python 3.9+
- Platform: macOS 10.13+ (High Sierra trở lên)
- Yêu cầu quyền: Root/Administrator privileges
- Không có budget cho third-party commercial libraries

**Assumptions:**
- Thiết bị đã được unlock và có quyền truy cập
- Hệ thống file: APFS (Apple File System)
- Python 3.9+ đã được cài đặt trên hệ thống phân tích
- Có ít nhất 500MB RAM và 1GB disk space khả dụng

---

## 2. Phân Tích Nghiệp Vụ

### 2.1 User Stories

#### Epic 1: FSEvents Collection & Parsing

**US-001: Thu thập FSEvents Database**
```
Là một Digital Forensics Investigator,
Tôi muốn thu thập toàn bộ FSEvents database từ thiết bị macOS đang chạy,
Để có thể phân tích lịch sử thay đổi file system mà không cần tạo disk image.

Acceptance Criteria:
- Tự động xác định vị trí FSEvents database trên tất cả APFS volumes
- Copy dữ liệu với hash verification (SHA-256)
- Không làm thay đổi dữ liệu gốc
- Ghi log timestamp và metadata của quá trình thu thập
```

**US-002: Parse FSEvents Binary Format**
```
Là một Forensics Analyst,
Tôi muốn giải mã định dạng binary của FSEvents,
Để có thể đọc được thông tin về các sự kiện file system.

Acceptance Criteria:
- Hỗ trợ FSEvents version 1 và 2 (DLS format)
- Xử lý được compressed và uncompressed streams
- Trích xuất đầy đủ: timestamp, path, event flags, node ID
- Xử lý lỗi gracefully với malformed data
```

**US-003: Lọc Events Đáng Ngờ**
```
Là một Incident Responder,
Tôi muốn lọc nhanh các events liên quan đến hoạt động đáng ngờ,
Để tập trung điều tra vào các mục tiêu ưu tiên cao.

Acceptance Criteria:
- Filter: ItemRemoved, ItemRenamed trong thư mục nhạy cảm
- Filter: Executables created/modified
- Filter: Files with suspicious extensions (.sh, .command, .app)
- Customizable filter rules via config file
```

#### Epic 2: Extended Attributes Analysis

**US-004: Trích xuất Extended Attributes**
```
Là một Forensics Investigator,
Tôi muốn trích xuất Extended Attributes từ files,
Để xác định nguồn gốc và đặc điểm bảo mật của files.

Acceptance Criteria:
- Đọc tất cả xattr của file/directory
- Đặc biệt focus vào: com.apple.quarantine, com.apple.metadata:kMDItemWhereFroms
- Decode quarantine flags và download sources
- Xử lý được files đã bị xóa nếu còn metadata
```

**US-005: Phân tích Download Sources**
```
Là một Security Analyst,
Tôi muốn xác định files được tải từ đâu,
Để đánh giá rủi ro và truy vết nguồn gốc malware.

Acceptance Criteria:
- Parse URL từ kMDItemWhereFroms
- Identify download method (browser, curl, AirDrop, etc.)
- Extract timestamp của download event
- Correlate với browser history nếu có
```

#### Epic 3: Timeline & Reporting

**US-006: Tạo Priority Timeline**
```
Là một Lead Investigator,
Tôi muốn có timeline tự động sắp xếp theo mức độ ưu tiên,
Để nhanh chóng xác định sequence of events trong incident.

Acceptance Criteria:
- Timeline sắp xếp theo timestamp
- Priority scoring dựa trên: event type, location, file type
- Highlight suspicious patterns (mass deletion, encryption events)
- Visualize timeline trong HTML report
```

**US-007: Xuất Báo Cáo Đa Định Dạng**
```
Là một Forensics Team Manager,
Tôi muốn xuất báo cáo dưới nhiều định dạng,
Để chia sẻ với các stakeholders khác nhau.

Acceptance Criteria:
- CSV export: cho data analysis tools
- JSON export: cho automation và API integration
- HTML report: cho presentation và documentation
- Include summary statistics và key findings
```

### 2.2 Use Case Diagrams

```
┌─────────────────────────────────────────────────────────────┐
│                    mFAA Use Case Diagram                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│    ┌──────────────┐                                         │
│    │  Forensics   │                                         │
│    │ Investigator │                                         │
│    └──────┬───────┘                                         │
│           │                                                  │
│           ├──────── Collect FSEvents                        │
│           │                                                  │
│           ├──────── Parse FSEvents                          │
│           │                                                  │
│           ├──────── Extract xattr                           │
│           │                                                  │
│           ├──────── Filter Suspicious Events                │
│           │                                                  │
│           ├──────── Generate Timeline                       │
│           │                                                  │
│           └──────── Export Reports                          │
│                                                              │
│    ┌──────────────┐                                         │
│    │   Security   │                                         │
│    │   Analyst    │                                         │
│    └──────┬───────┘                                         │
│           │                                                  │
│           ├──────── Analyze Download Sources                │
│           │                                                  │
│           ├──────── Identify Malware Artifacts              │
│           │                                                  │
│           └──────── Review Priority Events                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Business Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   Investigation Workflow                     │
└─────────────────────────────────────────────────────────────┘

    [Incident Detected]
            │
            ▼
    [Secure Device Access]
            │
            ▼
    ┌───────────────────┐
    │ Run mFAA Tool     │
    │ (Live Acquisition)│
    └─────────┬─────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │     Automated Collection Phase       │
    ├─────────────────────────────────────┤
    │ 1. Identify APFS volumes            │
    │ 2. Locate FSEvents databases        │
    │ 3. Hash and copy artifacts          │
    │ 4. Extract Extended Attributes      │
    │ 5. Collect system metadata          │
    └─────────┬───────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │      Parsing & Analysis Phase        │
    ├─────────────────────────────────────┤
    │ 1. Decompress FSEvents streams      │
    │ 2. Parse binary structures          │
    │ 3. Decode xattr values              │
    │ 4. Correlate events                 │
    │ 5. Apply filtering rules            │
    └─────────┬───────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │     Timeline Generation Phase        │
    ├─────────────────────────────────────┤
    │ 1. Sort events chronologically      │
    │ 2. Calculate priority scores        │
    │ 3. Identify suspicious patterns     │
    │ 4. Group related events             │
    └─────────┬───────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │       Reporting Phase                │
    ├─────────────────────────────────────┤
    │ 1. Generate CSV/JSON/HTML           │
    │ 2. Create executive summary         │
    │ 3. Package evidence files           │
    │ 4. Calculate checksums              │
    └─────────┬───────────────────────────┘
              │
              ▼
    [Evidence Analysis & Investigation]
            │
            ▼
    [Case Documentation & Legal Proceedings]
```

---

## 3. Yêu Cầu Chức Năng

### 3.1 Functional Requirements

#### FR-001: FSEvents Collection
- **Priority:** Must Have (P0)
- **Description:** Thu thập FSEvents database từ tất cả APFS volumes
- **Requirements:**
  - FR-001.1: Tự động detect và list tất cả mounted APFS volumes
  - FR-001.2: Locate FSEvents database tại `/.fseventsd/` cho mỗi volume
  - FR-001.3: Copy toàn bộ `.fseventsd` directory với preserved timestamps
  - FR-001.4: Calculate SHA-256 hash cho mỗi file thu thập
  - FR-001.5: Create acquisition log với metadata (timestamp, hostname, volume info)
  - FR-001.6: Handle permission errors gracefully
  - FR-001.7: Support offline volumes nếu được mount sau

#### FR-002: FSEvents Parsing
- **Priority:** Must Have (P0)
- **Description:** Parse và decode FSEvents binary format
- **Requirements:**
  - FR-002.1: Support FSEvents format version 1 (legacy)
  - FR-002.2: Support FSEvents format version 2 (DLS - gzip compressed)
  - FR-002.3: Extract: event ID, timestamp, path, flags, node ID
  - FR-002.4: Decode event flags theo Apple documentation:
    - Created, Removed, InodeMetaMod, Renamed, Modified
    - IsFile, IsDir, IsSymlink, IsHardlink
    - ItemCloned, ItemCreated, ItemRemoved, etc.
  - FR-002.5: Handle Unicode paths correctly
  - FR-002.6: Parse page headers và record structures
  - FR-002.7: Validate data integrity during parsing

#### FR-003: Extended Attributes Extraction
- **Priority:** Must Have (P0)
- **Description:** Trích xuất và phân tích Extended Attributes
- **Requirements:**
  - FR-003.1: Extract all xattr từ files/directories
  - FR-003.2: Priority xattr types:
    - `com.apple.quarantine` - quarantine flags
    - `com.apple.metadata:kMDItemWhereFroms` - download URLs
    - `com.apple.metadata:kMDItemDownloadedDate` - download timestamp
    - `com.apple.lastuseddate#PS` - last used date
  - FR-003.3: Decode quarantine flags (hex format):
    - Byte 0: Quarantine type (0000-0003)
    - Byte 1-4: Flags
    - Timestamp and UUID
  - FR-003.4: Extract URLs từ binary plist trong kMDItemWhereFroms
  - FR-003.5: Handle xattr trên files đã bị xóa (nếu metadata còn)

#### FR-004: Event Filtering
- **Priority:** Must Have (P0)
- **Description:** Lọc events dựa trên criteria
- **Requirements:**
  - FR-004.1: Filter by event type:
    - ItemRemoved (deleted files)
    - ItemRenamed
    - ItemCreated
    - ItemModified
  - FR-004.2: Filter by path patterns:
    - `/Users/*/Downloads/`
    - `/Applications/`
    - `/tmp/`, `/var/tmp/`
    - User-defined paths
  - FR-004.3: Filter by file extensions:
    - Executables: `.app`, `.command`, `.sh`, `.py`, `.jar`
    - Documents: `.pdf`, `.doc`, `.xls`
    - Archives: `.zip`, `.dmg`, `.pkg`
    - Suspicious: `.exe`, `.dll`, `.scr`
  - FR-004.4: Filter by time range (start date - end date)
  - FR-004.5: Configurable filter rules via YAML/JSON config file
  - FR-004.6: Combine multiple filters (AND/OR logic)

#### FR-005: Priority Scoring
- **Priority:** Should Have (P1)
- **Description:** Tính toán priority score cho events
- **Requirements:**
  - FR-005.1: Scoring algorithm factors:
    - Event type weight (Removed=10, Created=5, Modified=3)
    - Path sensitivity (System paths=10, User dirs=5)
    - File type risk (Executable=10, Script=8, Document=3)
    - Quarantine flag presence (+5)
    - Download from internet (+5)
  - FR-005.2: Score range: 0-100
  - FR-005.3: Categorize: Critical (80-100), High (60-79), Medium (40-59), Low (0-39)
  - FR-005.4: Customizable weights via config

#### FR-006: Timeline Generation
- **Priority:** Must Have (P0)
- **Description:** Tạo timeline từ events
- **Requirements:**
  - FR-006.1: Sort events chronologically
  - FR-006.2: Include fields: timestamp, event_type, path, priority, xattr_summary
  - FR-006.3: Group related events (rename sequences, multi-step operations)
  - FR-006.4: Detect patterns:
    - Mass deletion (>50 files in <1 minute)
    - Encryption ransomware pattern (many files renamed to .encrypted)
    - Data exfiltration (large files to external volumes)
  - FR-006.5: Timeline visualization options:
    - Text-based timeline (stdout)
    - CSV export
    - JSON export
    - HTML interactive timeline

#### FR-007: Report Generation
- **Priority:** Must Have (P0)
- **Description:** Xuất báo cáo phân tích
- **Requirements:**
  - FR-007.1: CSV Report:
    - All events với full details
    - Sortable và filterable
    - Compatible với Excel, Splunk, etc.
  - FR-007.2: JSON Report:
    - Structured data cho automation
    - Include metadata và statistics
    - Schema validation
  - FR-007.3: HTML Report:
    - Executive summary
    - Statistics dashboard
    - Interactive timeline
    - Suspicious events highlighted
    - Downloadable artifacts list
  - FR-007.4: Summary statistics:
    - Total events processed
    - Events by type breakdown
    - Files deleted count
    - High-priority events count
    - Suspicious patterns detected

#### FR-008: Command-Line Interface
- **Priority:** Must Have (P0)
- **Description:** CLI interface cho automation
- **Requirements:**
  - FR-008.1: Commands:
    - `mfaa collect` - collect artifacts
    - `mfaa parse` - parse collected data
    - `mfaa analyze` - full analysis pipeline
    - `mfaa report` - generate reports only
  - FR-008.2: Options:
    - `--volume` - specify volume to analyze
    - `--output-dir` - output directory
    - `--format` - report format (csv, json, html, all)
    - `--filter-config` - path to filter config
    - `--time-range` - specify time range
    - `--verbose` - detailed logging
  - FR-008.3: Exit codes:
    - 0 = Success
    - 1 = General error
    - 2 = Permission denied
    - 3 = Invalid input
  - FR-008.4: Progress indicators cho long-running operations

### 3.2 Non-Functional Requirements

#### NFR-001: Performance
- Parse speed: ≥ 10,000 FSEvents per second
- Memory usage: ≤ 500MB for typical dataset (1M events)
- Startup time: ≤ 2 seconds
- Report generation: ≤ 5 seconds for 100K events

#### NFR-002: Reliability
- Crash rate: 0% trên well-formed data
- Graceful error handling cho malformed data
- Data integrity verification (checksums)
- Atomic operations (all-or-nothing)

#### NFR-003: Maintainability
- Code documentation: 100% public APIs
- Modular architecture
- Unit test coverage: ≥ 85%
- Follow PEP 8 style guide
- Type hints for all functions

#### NFR-004: Security
- No data modification on source system
- Read-only operations
- Secure handling of sensitive paths
- Hash verification for collected data
- Audit logging

#### NFR-005: Compatibility
- Python 3.9, 3.10, 3.11, 3.12
- macOS 10.13 (High Sierra) to macOS 15 (Sequoia)
- APFS volumes only
- Both Intel and Apple Silicon architectures

#### NFR-006: Usability
- Clear error messages with remediation steps
- Comprehensive help documentation
- Example configurations included
- Setup wizard for first-time users

---

## 4. Kiến Trúc Hệ Thống

### 4.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    mFAA Architecture Diagram                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  mfaa (main entry point)                                  │  │
│  │  - ArgumentParser                                         │  │
│  │  - Command dispatcher                                     │  │
│  │  - Configuration loader                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     Core Modules Layer                           │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Collector      │  │  Parser         │  │  Analyzer      │  │
│  │  Module         │  │  Module         │  │  Module        │  │
│  ├─────────────────┤  ├─────────────────┤  ├────────────────┤  │
│  │ - VolumeScanner │  │ - FSEventsParser│  │ - EventFilter  │  │
│  │ - ArtifactCopy  │  │ - XattrParser   │  │ - PriorityScore│  │
│  │ - HashCalc      │  │ - GzipHandler   │  │ - PatternDetect│  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Timeline       │  │  Reporter       │  │  Utils         │  │
│  │  Module         │  │  Module         │  │  Module        │  │
│  ├─────────────────┤  ├─────────────────┤  ├────────────────┤  │
│  │ - TimelineGen   │  │ - CSVReporter   │  │ - Logger       │  │
│  │ - EventGrouper  │  │ - JSONReporter  │  │ - ConfigLoader │  │
│  │ - Correlator    │  │ - HTMLReporter  │  │ - Validator    │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Models (Python dataclasses)                        │  │
│  │  - FSEvent, XattrRecord, TimelineEntry, Report           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Storage                                                  │  │
│  │  - Local filesystem (collected artifacts)                │  │
│  │  - SQLite (optional - for large datasets)                │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                    External Dependencies                          │
│  - Python stdlib (pathlib, struct, gzip, hashlib)                │
│  - click (CLI framework)                                          │
│  - pyyaml (config files)                                          │
│  - jinja2 (HTML templates)                                        │
└───────────────────────────────────────────────────────────────────┘
```

### 4.2 Module Design

#### Module 1: Collector (`mfaa/collector/`)

**Purpose:** Thu thập artifacts từ macOS system

**Components:**
```python
collector/
├── __init__.py
├── volume_scanner.py      # Scan và identify APFS volumes
├── fsevents_collector.py  # Collect FSEvents databases
├── xattr_collector.py     # Collect Extended Attributes
└── hash_calculator.py     # Calculate checksums
```

**Key Classes:**
- `VolumeScanner`: Detect mounted APFS volumes
- `FSEventsCollector`: Copy .fseventsd directories
- `XattrCollector`: Extract xattr từ files
- `HashCalculator`: Generate SHA-256 hashes

#### Module 2: Parser (`mfaa/parser/`)

**Purpose:** Parse binary formats

**Components:**
```python
parser/
├── __init__.py
├── fsevents_parser.py     # Parse FSEvents binary
├── xattr_parser.py        # Decode Extended Attributes
├── gzip_handler.py        # Handle compressed streams
└── structures.py          # Binary structure definitions
```

**Key Classes:**
- `FSEventsParser`: Parse FSEvents v1 và v2
- `XattrParser`: Decode xattr values
- `GzipHandler`: Decompress gzip streams
- `FSEventsStructure`: Binary struct definitions

#### Module 3: Analyzer (`mfaa/analyzer/`)

**Purpose:** Analyze và filter events

**Components:**
```python
analyzer/
├── __init__.py
├── event_filter.py        # Filter events
├── priority_scorer.py     # Calculate priority scores
├── pattern_detector.py    # Detect suspicious patterns
└── correlator.py          # Correlate related events
```

**Key Classes:**
- `EventFilter`: Apply filtering rules
- `PriorityScorer`: Calculate event priorities
- `PatternDetector`: Detect ransomware, data exfil, etc.
- `EventCorrelator`: Group related events

#### Module 4: Timeline (`mfaa/timeline/`)

**Purpose:** Generate chronological timeline

**Components:**
```python
timeline/
├── __init__.py
├── generator.py           # Timeline generation
├── grouper.py            # Group related events
└── visualizer.py         # Visualization helpers
```

#### Module 5: Reporter (`mfaa/reporter/`)

**Purpose:** Generate reports

**Components:**
```python
reporter/
├── __init__.py
├── base_reporter.py       # Abstract base class
├── csv_reporter.py        # CSV export
├── json_reporter.py       # JSON export
├── html_reporter.py       # HTML report
└── templates/            # Jinja2 templates
    └── report.html.j2
```

#### Module 6: Utils (`mfaa/utils/`)

**Purpose:** Utilities và helpers

**Components:**
```python
utils/
├── __init__.py
├── logger.py              # Logging setup
├── config.py              # Configuration management
├── validator.py           # Input validation
└── exceptions.py          # Custom exceptions
```

### 4.3 Data Flow

```
┌──────────────┐
│ macOS Device │
└──────┬───────┘
       │
       │ 1. Scan volumes
       ▼
┌─────────────────┐
│ VolumeScanner   │
└──────┬──────────┘
       │
       │ 2. Collect artifacts
       ▼
┌─────────────────┐
│ Collector       │───────► [Raw FSEvents Files]
└──────┬──────────┘         [Xattr Data]
       │                    [Checksums]
       │
       │ 3. Parse
       ▼
┌─────────────────┐
│ Parser          │───────► [FSEvent Objects]
└──────┬──────────┘         [Xattr Objects]
       │
       │ 4. Analyze
       ▼
┌─────────────────┐
│ Analyzer        │───────► [Filtered Events]
└──────┬──────────┘         [Priority Scores]
       │                    [Patterns Detected]
       │
       │ 5. Generate Timeline
       ▼
┌─────────────────┐
│ Timeline Gen    │───────► [Chronological Timeline]
└──────┬──────────┘         [Grouped Events]
       │
       │ 6. Report
       ▼
┌─────────────────┐
│ Reporter        │───────► [CSV Report]
└─────────────────┘         [JSON Report]
                            [HTML Report]
```

---

## 5. Đặc Tả API

### 5.1 Core API Documentation

#### 5.1.1 Collector API

##### `VolumeScanner`

```python
class VolumeScanner:
    """Scan và identify APFS volumes trên hệ thống."""
    
    def scan_volumes(self) -> List[VolumeInfo]:
        """
        Scan tất cả mounted volumes và return APFS volumes.
        
        Returns:
            List[VolumeInfo]: List các APFS volumes với metadata
            
        Raises:
            PermissionError: Nếu không có quyền read
            OSError: Nếu không thể access volume
            
        Example:
            >>> scanner = VolumeScanner()
            >>> volumes = scanner.scan_volumes()
            >>> for vol in volumes:
            ...     print(f"{vol.name}: {vol.mount_point}")
        """
        
    def get_volume_info(self, mount_point: str) -> VolumeInfo:
        """
        Lấy detailed info về một volume.
        
        Args:
            mount_point: Path tới volume mount point
            
        Returns:
            VolumeInfo: Detailed volume information
            
        Example:
            >>> info = scanner.get_volume_info("/Volumes/Macintosh HD")
            >>> print(info.filesystem_type)  # "apfs"
        """
```

##### `FSEventsCollector`

```python
class FSEventsCollector:
    """Collect FSEvents database từ volumes."""
    
    def __init__(self, output_dir: Path, verify_hashes: bool = True):
        """
        Initialize FSEvents collector.
        
        Args:
            output_dir: Directory để lưu collected artifacts
            verify_hashes: Có calculate SHA-256 hashes không
        """
    
    def collect(self, volume: VolumeInfo) -> CollectionResult:
        """
        Collect FSEvents database từ một volume.
        
        Args:
            volume: VolumeInfo object từ VolumeScanner
            
        Returns:
            CollectionResult: Kết quả collection với metadata
            
        Raises:
            PermissionError: Không có quyền access .fseventsd
            FileNotFoundError: .fseventsd không tồn tại
            IOError: Lỗi khi copy files
            
        Example:
            >>> collector = FSEventsCollector(Path("/output"))
            >>> result = collector.collect(volume)
            >>> print(f"Collected {result.files_copied} files")
            >>> print(f"SHA-256: {result.checksums}")
        """
    
    def collect_all_volumes(self) -> List[CollectionResult]:
        """
        Collect từ tất cả APFS volumes được detect.
        
        Returns:
            List[CollectionResult]: Kết quả cho mỗi volume
        """
```

##### `XattrCollector`

```python
class XattrCollector:
    """Collect Extended Attributes từ files."""
    
    def collect_xattr(self, file_path: Path) -> XattrRecord:
        """
        Collect tất cả xattr từ một file.
        
        Args:
            file_path: Path tới file cần collect xattr
            
        Returns:
            XattrRecord: Record chứa tất cả xattr
            
        Example:
            >>> collector = XattrCollector()
            >>> xattr = collector.collect_xattr(Path("/path/to/file.dmg"))
            >>> if xattr.has_quarantine:
            ...     print(f"Downloaded from: {xattr.download_url}")
        """
    
    def collect_directory(self, 
                         dir_path: Path, 
                         recursive: bool = True) -> List[XattrRecord]:
        """
        Collect xattr từ tất cả files trong directory.
        
        Args:
            dir_path: Directory path
            recursive: Có scan subdirectories không
            
        Returns:
            List[XattrRecord]: List xattr records
        """
```

#### 5.1.2 Parser API

##### `FSEventsParser`

```python
class FSEventsParser:
    """Parse FSEvents binary format."""
    
    def __init__(self, version: Optional[int] = None):
        """
        Initialize parser.
        
        Args:
            version: FSEvents format version (1 hoặc 2). 
                    None = auto-detect
        """
    
    def parse_file(self, file_path: Path) -> List[FSEvent]:
        """
        Parse một FSEvents file.
        
        Args:
            file_path: Path tới FSEvents file (có thể compressed)
            
        Returns:
            List[FSEvent]: List các FSEvent objects
            
        Raises:
            ParseError: Nếu file format invalid
            CompressionError: Nếu không decompress được
            
        Example:
            >>> parser = FSEventsParser()
            >>> events = parser.parse_file(Path("0000000002d5bfc3"))
            >>> for event in events:
            ...     if event.is_removed:
            ...         print(f"Deleted: {event.path}")
        """
    
    def parse_directory(self, fsevents_dir: Path) -> List[FSEvent]:
        """
        Parse toàn bộ .fseventsd directory.
        
        Args:
            fsevents_dir: Path tới .fseventsd directory
            
        Returns:
            List[FSEvent]: Tất cả events từ tất cả files
        """
    
    @staticmethod
    def decode_flags(flags: int) -> EventFlags:
        """
        Decode event flags integer thành EventFlags object.
        
        Args:
            flags: Raw flags integer từ FSEvents
            
        Returns:
            EventFlags: Decoded flags object
            
        Example:
            >>> flags = parser.decode_flags(0x00001001)
            >>> print(flags.is_file)  # True
            >>> print(flags.is_created)  # True
        """
```

##### `XattrParser`

```python
class XattrParser:
    """Parse và decode Extended Attributes values."""
    
    @staticmethod
    def parse_quarantine(value: bytes) -> QuarantineInfo:
        """
        Parse com.apple.quarantine attribute.
        
        Args:
            value: Raw bytes của quarantine xattr
            
        Returns:
            QuarantineInfo: Decoded quarantine information
            
        Format: "0083;673a8f2d;Safari;F643CD5F-6974-46AB-8A9B-C7A7E9C4F8F7"
        - 0083: Flags (hex)
        - 673a8f2d: Timestamp (hex)
        - Safari: Source application
        - UUID: Unique identifier
            
        Example:
            >>> info = XattrParser.parse_quarantine(xattr_value)
            >>> print(info.timestamp)  # datetime object
            >>> print(info.source_app)  # "Safari"
            >>> print(info.is_web_download)  # True
        """
    
    @staticmethod
    def parse_download_source(value: bytes) -> List[str]:
        """
        Parse kMDItemWhereFroms attribute (binary plist).
        
        Args:
            value: Raw bytes của WhereFroms xattr
            
        Returns:
            List[str]: List URLs nơi file được download
            
        Example:
            >>> urls = XattrParser.parse_download_source(xattr_value)
            >>> print(urls)
            ['https://example.com/malware.dmg', 
             'https://example.com/referrer']
        """
```

#### 5.1.3 Analyzer API

##### `EventFilter`

```python
class EventFilter:
    """Filter events dựa trên criteria."""
    
    def __init__(self, config: FilterConfig):
        """
        Initialize filter với configuration.
        
        Args:
            config: FilterConfig object với filter rules
        """
    
    def filter_events(self, events: List[FSEvent]) -> List[FSEvent]:
        """
        Apply tất cả filter rules lên events.
        
        Args:
            events: List FSEvents cần filter
            
        Returns:
            List[FSEvent]: Filtered events
            
        Example:
            >>> config = FilterConfig.from_yaml("filters.yaml")
            >>> filter = EventFilter(config)
            >>> filtered = filter.filter_events(all_events)
            >>> print(f"Filtered to {len(filtered)} suspicious events")
        """
    
    def filter_by_type(self, 
                       events: List[FSEvent], 
                       event_types: List[str]) -> List[FSEvent]:
        """
        Filter by event types (Created, Removed, etc.).
        """
    
    def filter_by_path(self, 
                      events: List[FSEvent], 
                      path_patterns: List[str]) -> List[FSEvent]:
        """
        Filter by path patterns (regex supported).
        """
    
    def filter_by_extension(self, 
                           events: List[FSEvent], 
                           extensions: List[str]) -> List[FSEvent]:
        """
        Filter by file extensions.
        """
    
    def filter_by_timerange(self, 
                           events: List[FSEvent], 
                           start: datetime, 
                           end: datetime) -> List[FSEvent]:
        """
        Filter by timestamp range.
        """
```

##### `PriorityScorer`

```python
class PriorityScorer:
    """Calculate priority scores cho events."""
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        """
        Initialize scorer với custom weights.
        
        Args:
            weights: Custom scoring weights. None = use defaults
        """
    
    def calculate_score(self, event: FSEvent) -> int:
        """
        Calculate priority score (0-100) cho một event.
        
        Args:
            event: FSEvent object
            
        Returns:
            int: Priority score (0-100)
            
        Scoring factors:
        - Event type (Removed=10, Created=5, Modified=3)
        - Path sensitivity (System=10, Applications=8, User=5)
        - File type risk (Executable=10, Script=8, Document=3)
        - Has quarantine flag (+5)
        - Downloaded from internet (+5)
            
        Example:
            >>> scorer = PriorityScorer()
            >>> score = scorer.calculate_score(event)
            >>> if score >= 80:
            ...     print("CRITICAL: Requires immediate attention")
        """
    
    def score_batch(self, events: List[FSEvent]) -> List[Tuple[FSEvent, int]]:
        """
        Score multiple events efficiently.
        
        Returns:
            List[Tuple[FSEvent, int]]: (event, score) pairs
        """
    
    @staticmethod
    def categorize_priority(score: int) -> str:
        """
        Categorize score thành priority level.
        
        Returns:
            str: "CRITICAL", "HIGH", "MEDIUM", or "LOW"
        """
```

##### `PatternDetector`

```python
class PatternDetector:
    """Detect suspicious patterns trong events."""
    
    def detect_mass_deletion(self, 
                           events: List[FSEvent], 
                           threshold: int = 50,
                           time_window: int = 60) -> List[Pattern]:
        """
        Detect mass file deletion (potential ransomware).
        
        Args:
            events: List events cần analyze
            threshold: Minimum số files deleted để trigger
            time_window: Time window in seconds
            
        Returns:
            List[Pattern]: Detected patterns
            
        Example:
            >>> detector = PatternDetector()
            >>> patterns = detector.detect_mass_deletion(events)
            >>> for pattern in patterns:
            ...     print(f"Mass deletion: {pattern.file_count} files")
            ...     print(f"Time: {pattern.start_time} - {pattern.end_time}")
        """
    
    def detect_encryption_activity(self, 
                                   events: List[FSEvent]) -> List[Pattern]:
        """
        Detect encryption patterns (ransomware indicator).
        
        Indicators:
        - Files renamed với suspicious extensions (.encrypted, .locked)
        - Rapid file modifications
        - Creation of ransom notes
        """
    
    def detect_data_exfiltration(self, 
                                events: List[FSEvent]) -> List[Pattern]:
        """
        Detect potential data exfiltration.
        
        Indicators:
        - Large files copied to external volumes
        - Archive creation followed by external transfer
        - Copying of sensitive file types (documents, databases)
        """
    
    def detect_persistence_mechanisms(self, 
                                     events: List[FSEvent]) -> List[Pattern]:
        """
        Detect malware persistence mechanisms.
        
        Indicators:
        - LaunchAgents/LaunchDaemons created
        - Login items modified
        - Shell profiles modified (.bash_profile, .zshrc)
        """
```

#### 5.1.4 Reporter API

##### `CSVReporter`

```python
class CSVReporter:
    """Generate CSV reports."""
    
    def generate(self, 
                timeline: Timeline, 
                output_path: Path,
                include_all: bool = True) -> None:
        """
        Generate CSV report.
        
        Args:
            timeline: Timeline object với events
            output_path: Output file path
            include_all: Include tất cả events hay chỉ high-priority
            
        CSV Columns:
        - timestamp
        - event_type
        - path
        - priority_score
        - priority_category
        - flags
        - node_id
        - xattr_quarantine
        - xattr_download_url
        - notes
            
        Example:
            >>> reporter = CSVReporter()
            >>> reporter.generate(timeline, Path("report.csv"))
        """
```

##### `JSONReporter`

```python
class JSONReporter:
    """Generate JSON reports."""
    
    def generate(self, 
                timeline: Timeline, 
                output_path: Path,
                pretty: bool = True) -> None:
        """
        Generate JSON report.
        
        Args:
            timeline: Timeline object
            output_path: Output file path
            pretty: Pretty-print JSON
            
        JSON Structure:
        {
          "metadata": {
            "tool_version": "1.0.0",
            "generation_time": "2025-10-26T10:30:00Z",
            "volumes_analyzed": [...],
            "total_events": 125000,
            "critical_events": 45
          },
          "statistics": {
            "event_types": {...},
            "priority_distribution": {...},
            "patterns_detected": [...]
          },
          "timeline": [
            {
              "timestamp": "2025-10-25T14:23:45Z",
              "event_type": "ItemRemoved",
              "path": "/Users/user/Documents/secret.pdf",
              "priority": 85,
              "xattr": {...}
            },
            ...
          ]
        }
        """
```

##### `HTMLReporter`

```python
class HTMLReporter:
    """Generate interactive HTML reports."""
    
    def generate(self, 
                timeline: Timeline, 
                output_path: Path,
                template: Optional[Path] = None) -> None:
        """
        Generate HTML report với interactive timeline.
        
        Args:
            timeline: Timeline object
            output_path: Output HTML file path
            template: Custom Jinja2 template path (optional)
            
        Features:
        - Executive summary dashboard
        - Statistics charts (Chart.js)
        - Interactive timeline với filtering
        - Suspicious events highlighted
        - Downloadable CSV/JSON exports
        - Search functionality
            
        Example:
            >>> reporter = HTMLReporter()
            >>> reporter.generate(timeline, Path("report.html"))
            # Opens in browser automatically
        """
```

### 5.2 Data Models

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, Flag
from pathlib import Path
from typing import Optional, List, Dict

# ============================================================================
# Volume Information
# ============================================================================

@dataclass
class VolumeInfo:
    """Information about an APFS volume."""
    name: str
    mount_point: Path
    filesystem_type: str  # "apfs"
    device_node: str  # "/dev/disk3s1"
    total_size: int  # bytes
    available_size: int  # bytes
    encryption_enabled: bool
    
# ============================================================================
# FSEvents
# ============================================================================

class EventType(Enum):
    """FSEvents event types."""
    CREATED = "Created"
    REMOVED = "Removed"
    MODIFIED = "Modified"
    RENAMED = "Renamed"
    INODE_META_MOD = "InodeMetaMod"
    FINDER_INFO_MOD = "FinderInfoMod"
    CHANGE_OWNER = "ChangeOwner"
    XATTR_MOD = "XAttrMod"
    IS_FILE = "IsFile"
    IS_DIR = "IsDir"
    IS_SYMLINK = "IsSymlink"
    IS_HARDLINK = "IsHardlink"
    ITEM_CLONED = "ItemCloned"

class EventFlags(Flag):
    """FSEvents flags (bitfield)."""
    NONE = 0
    MUST_SCAN_SUBDIRS = 0x00000001
    USER_DROPPED = 0x00000002
    KERNEL_DROPPED = 0x00000004
    EVENT_IDS_WRAPPED = 0x00000008
    HISTORY_DONE = 0x00000010
    ROOT_CHANGED = 0x00000020
    MOUNT = 0x00000040
    UNMOUNT = 0x00000080
    ITEM_CREATED = 0x00000100
    ITEM_REMOVED = 0x00000200
    ITEM_INODE_META_MOD = 0x00000400
    ITEM_RENAMED = 0x00000800
    ITEM_MODIFIED = 0x00001000
    ITEM_FINDER_INFO_MOD = 0x00002000
    ITEM_CHANGE_OWNER = 0x00004000
    ITEM_XATTR_MOD = 0x00008000
    ITEM_IS_FILE = 0x00010000
    ITEM_IS_DIR = 0x00020000
    ITEM_IS_SYMLINK = 0x00040000
    ITEM_IS_HARDLINK = 0x00100000
    ITEM_CLONED = 0x00400000

@dataclass
class FSEvent:
    """A single FSEvents record."""
    event_id: int
    timestamp: datetime
    path: Path
    flags: EventFlags
    node_id: Optional[int] = None  # inode number
    
    # Derived properties
    @property
    def is_created(self) -> bool:
        return EventFlags.ITEM_CREATED in self.flags
    
    @property
    def is_removed(self) -> bool:
        return EventFlags.ITEM_REMOVED in self.flags
    
    @property
    def is_modified(self) -> bool:
        return EventFlags.ITEM_MODIFIED in self.flags
    
    @property
    def is_renamed(self) -> bool:
        return EventFlags.ITEM_RENAMED in self.flags
    
    @property
    def is_file(self) -> bool:
        return EventFlags.ITEM_IS_FILE in self.flags
    
    @property
    def is_directory(self) -> bool:
        return EventFlags.ITEM_IS_DIR in self.flags
    
    @property
    def event_types(self) -> List[EventType]:
        """Return list of event types for this event."""
        types = []
        if self.is_created:
            types.append(EventType.CREATED)
        if self.is_removed:
            types.append(EventType.REMOVED)
        if self.is_modified:
            types.append(EventType.MODIFIED)
        if self.is_renamed:
            types.append(EventType.RENAMED)
        # ... etc
        return types

# ============================================================================
# Extended Attributes
# ============================================================================

@dataclass
class QuarantineInfo:
    """Decoded com.apple.quarantine attribute."""
    flags: int  # quarantine flags
    timestamp: datetime  # when quarantined
    source_app: str  # "Safari", "Chrome", etc.
    uuid: str  # unique identifier
    
    @property
    def is_web_download(self) -> bool:
        """Check if file was downloaded from internet."""
        return (self.flags & 0x0080) != 0
    
    @property
    def is_safe_source(self) -> bool:
        """Check if from known safe source."""
        return (self.flags & 0x0001) != 0

@dataclass
class XattrRecord:
    """Extended Attributes for a file."""
    file_path: Path
    attributes: Dict[str, bytes]  # raw xattr key-value pairs
    
    # Parsed attributes
    quarantine_info: Optional[QuarantineInfo] = None
    download_urls: Optional[List[str]] = None
    download_timestamp: Optional[datetime] = None
    last_used_date: Optional[datetime] = None
    
    @property
    def has_quarantine(self) -> bool:
        return self.quarantine_info is not None
    
    @property
    def is_downloaded(self) -> bool:
        return self.download_urls is not None and len(self.download_urls) > 0

# ============================================================================
# Analysis Results
# ============================================================================

@dataclass
class Pattern:
    """Detected suspicious pattern."""
    pattern_type: str  # "mass_deletion", "encryption", "exfiltration"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    start_time: datetime
    end_time: datetime
    event_count: int
    affected_paths: List[Path]
    description: str
    indicators: Dict[str, any]  # additional pattern-specific data

@dataclass
class TimelineEntry:
    """Entry trong timeline."""
    event: FSEvent
    priority_score: int
    priority_category: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    xattr: Optional[XattrRecord] = None
    related_events: List[FSEvent] = None  # grouped events
    notes: List[str] = None  # analyst notes

@dataclass
class Timeline:
    """Complete timeline của analysis."""
    entries: List[TimelineEntry]
    patterns: List[Pattern]
    statistics: Dict[str, any]
    metadata: Dict[str, any]
    
    def sort_chronological(self) -> None:
        """Sort entries by timestamp."""
        self.entries.sort(key=lambda e: e.event.timestamp)
    
    def filter_by_priority(self, min_score: int) -> List[TimelineEntry]:
        """Return entries with score >= min_score."""
        return [e for e in self.entries if e.priority_score >= min_score]

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class FilterConfig:
    """Configuration for event filtering."""
    event_types: List[str]  # ["ItemRemoved", "ItemCreated"]
    path_patterns: List[str]  # regex patterns
    extensions: List[str]  # [".sh", ".command", ".app"]
    time_range: Optional[tuple[datetime, datetime]] = None
    min_priority: Optional[int] = None
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'FilterConfig':
        """Load configuration from YAML file."""
        pass

@dataclass
class ScoringWeights:
    """Weights for priority scoring."""
    event_type_weights: Dict[str, int]  # {"Removed": 10, "Created": 5}
    path_weights: Dict[str, int]  # {"/System": 10, "/Applications": 8}
    file_type_weights: Dict[str, int]  # {".app": 10, ".sh": 8}
    quarantine_bonus: int = 5
    download_bonus: int = 5

# ============================================================================
# Results
# ============================================================================

@dataclass
class CollectionResult:
    """Result of artifact collection."""
    volume: VolumeInfo
    collection_time: datetime
    output_directory: Path
    files_copied: int
    total_size: int  # bytes
    checksums: Dict[str, str]  # filename -> SHA-256
    errors: List[str]
    success: bool
```

### 5.3 Configuration Files

#### Filter Configuration (YAML)

```yaml
# filters.yaml - Event filtering configuration

# Event types to include (empty = all)
event_types:
  - ItemRemoved
  - ItemCreated
  - ItemRenamed
  - ItemModified

# Path patterns (regex supported)
paths:
  include:
    - "^/Users/.*/Downloads/"
    - "^/Applications/"
    - "^/tmp/"
    - "^/var/tmp/"
    - "^/Users/.*/Library/LaunchAgents/"
    - "^/Library/LaunchDaemons/"
  exclude:
    - "^/System/Library/"  # exclude system files
    - "^/private/var/log/"  # exclude logs

# File extensions to focus on
extensions:
  executables:
    - .app
    - .command
    - .sh
    - .py
    - .pl
    - .rb
    - .jar
  documents:
    - .pdf
    - .doc
    - .docx
    - .xls
    - .xlsx
  archives:
    - .zip
    - .dmg
    - .pkg
    - .tar
    - .gz
  suspicious:
    - .exe
    - .dll
    - .scr
    - .encrypted
    - .locked

# Time range filter (optional)
time_range:
  start: "2025-10-01T00:00:00Z"
  end: "2025-10-26T23:59:59Z"

# Minimum priority score (0-100)
min_priority: 40
```

#### Scoring Configuration (YAML)

```yaml
# scoring.yaml - Priority scoring weights

# Event type weights (0-10)
event_types:
  ItemRemoved: 10
  ItemCreated: 5
  ItemRenamed: 7
  ItemModified: 3
  XAttrMod: 4
  ChangeOwner: 6

# Path sensitivity weights (0-10)
paths:
  "^/System/": 10
  "^/Library/LaunchDaemons/": 10
  "^/Users/.*/Library/LaunchAgents/": 9
  "^/Applications/": 8
  "^/Users/.*/Downloads/": 7
  "^/Users/": 5
  "^/tmp/": 6
  "^/var/tmp/": 6

# File type risk weights (0-10)
file_types:
  .app: 10
  .command: 10
  .sh: 9
  .py: 7
  .pl: 7
  .jar: 8
  .exe: 10
  .dll: 10
  .pdf: 3
  .doc: 3
  .zip: 6
  .dmg: 7

# Bonus points
bonuses:
  has_quarantine_flag: 5
  downloaded_from_internet: 5
  in_sensitive_location: 10

# Priority categories
categories:
  critical:
    min_score: 80
    max_score: 100
  high:
    min_score: 60
    max_score: 79
  medium:
    min_score: 40
    max_score: 59
  low:
    min_score: 0
    max_score: 39
```

---

## 6. Data Models

*(Đã được cover trong Section 5.2)*

---

## 7. Lộ Trình Phát Triển

### 7.1 4-Week Development Plan

#### **Tuần 1: Foundation & Research (26/10 - 01/11)**

**Mục tiêu:** Thiết lập project structure, nghiên cứu FSEvents format, implement basic parsing

**Deliverables:**
- ✅ Project repository setup (Git, .gitignore, README)
- ✅ Development environment (Python 3.9+, dependencies)
- ✅ Research documentation về FSEvents format
- ✅ Basic project structure (modules, packages)
- ✅ FSEvents parser prototype (read v1 format)
- ✅ Unit tests cho parser
- ✅ CI/CD pipeline setup (GitHub Actions)

**Tasks:**

**Day 1-2 (Thứ 7-CN):**
- [ ] Initialize Git repository
- [ ] Create project structure:
  ```
  mfaa/
  ├── mfaa/
  │   ├── __init__.py
  │   ├── cli.py
  │   ├── collector/
  │   ├── parser/
  │   ├── analyzer/
  │   ├── timeline/
  │   ├── reporter/
  │   └── utils/
  ├── tests/
  ├── docs/
  ├── examples/
  ├── requirements.txt
  ├── setup.py
  └── README.md
  ```
- [ ] Setup virtual environment
- [ ] Install dependencies: click, pyyaml, jinja2

**Day 3-4 (T2-T3):**
- [ ] Research FSEvents format:
  - Study Apple's FSEvents documentation
  - Analyze existing parsers (mac_apt, FSEventsParser)
  - Document v1 vs v2 format differences
  - Create test data samples
- [ ] Design binary structures (structs)
- [ ] Document findings trong `docs/fsevents_format.md`

**Day 5-6 (T4-T5):**
- [ ] Implement `parser/structures.py`:
  - FSEvents page header structure
  - Record structure
  - Flag definitions
- [ ] Implement `parser/fsevents_parser.py`:
  - `FSEventsParser` class
  - `parse_file()` method (v1 format first)
  - Flag decoding
  - Path extraction
- [ ] Write unit tests

**Day 7 (T6):**
- [ ] Code review và refactoring
- [ ] Documentation
- [ ] Setup CI/CD (pytest, coverage)
- [ ] Week 1 demo/review

**Week 1 Success Metrics:**
- ✅ Can parse FSEvents v1 format files
- ✅ Extract: timestamp, path, flags
- ✅ Unit test coverage ≥ 80%
- ✅ Clear documentation

---

#### **Tuần 2: Core Functionality (02/11 - 08/11)**

**Mục tiêu:** Complete collector, enhance parser (v2 + gzip), implement xattr extraction

**Deliverables:**
- ✅ VolumeScanner implementation
- ✅ FSEventsCollector implementation
- ✅ FSEvents v2 format support (gzip compressed)
- ✅ XattrCollector implementation
- ✅ XattrParser (quarantine, download sources)
- ✅ Integration tests

**Tasks:**

**Day 1-2 (T7-CN):**
- [ ] Implement `collector/volume_scanner.py`:
  - Detect mounted volumes
  - Filter APFS volumes
  - Extract volume metadata
- [ ] Implement `collector/fsevents_collector.py`:
  - Locate .fseventsd directories
  - Copy files with preserved metadata
  - Calculate SHA-256 hashes
- [ ] Write tests

**Day 3-4 (T2-T3):**
- [ ] Enhance FSEvents parser:
  - Add v2 format support
  - Implement `parser/gzip_handler.py`
  - Handle compressed streams
  - Auto-detect version
- [ ] Test với real macOS 12+ data
- [ ] Performance optimization

**Day 5-6 (T4-T5):**
- [ ] Implement `collector/xattr_collector.py`:
  - Extract xattr từ files
  - Batch processing
  - Error handling
- [ ] Implement `parser/xattr_parser.py`:
  - Parse quarantine flags
  - Decode download URLs (binary plist)
  - Parse timestamps
- [ ] Write comprehensive tests

**Day 7 (T6):**
- [ ] Integration testing
- [ ] Performance benchmarking
- [ ] Code review
- [ ] Week 2 demo

**Week 2 Success Metrics:**
- ✅ Can collect from live macOS system
- ✅ Parse both v1 and v2 FSEvents
- ✅ Extract and decode xattr
- ✅ Processing speed ≥ 5,000 events/sec
- ✅ Test coverage ≥ 85%

---

#### **Tuần 3: Analysis & Intelligence (09/11 - 15/11)**

**Mục tiêu:** Implement filtering, priority scoring, pattern detection, timeline generation

**Deliverables:**
- ✅ EventFilter với customizable rules
- ✅ PriorityScorer implementation
- ✅ PatternDetector (ransomware, exfiltration patterns)
- ✅ TimelineGenerator
- ✅ CLI interface (basic)

**Tasks:**

**Day 1-2 (T7-CN):**
- [ ] Implement `analyzer/event_filter.py`:
  - Filter by type, path, extension
  - Time range filtering
  - Config file support (YAML)
- [ ] Create default filter configs
- [ ] Write tests với various scenarios

**Day 3-4 (T2-T3):**
- [ ] Implement `analyzer/priority_scorer.py`:
  - Scoring algorithm
  - Configurable weights
  - Priority categorization
- [ ] Implement `analyzer/pattern_detector.py`:
  - Mass deletion detection
  - Encryption activity detection
  - Data exfiltration detection
  - Persistence mechanism detection
- [ ] Test với malware samples (simulated)

**Day 5-6 (T4-T5):**
- [ ] Implement `timeline/generator.py`:
  - Sort events chronologically
  - Group related events
  - Calculate statistics
- [ ] Implement `timeline/correlator.py`:
  - Correlate FSEvents với xattr
  - Identify event sequences
- [ ] Write tests

**Day 7 (T6):**
- [ ] Implement basic CLI (`cli.py`):
  - `mfaa analyze` command
  - Command-line arguments
  - Progress indicators
- [ ] Integration testing
- [ ] Week 3 demo

**Week 3 Success Metrics:**
- ✅ Can filter 1M events trong < 5 seconds
- ✅ Priority scoring accuracy validated
- ✅ Detect ransomware patterns trong test data
- ✅ Generate timeline từ real data
- ✅ CLI functional cho basic use cases

---

#### **Tuần 4: Reporting & Finalization (16/11 - 22/11)**

**Mục tiêu:** Complete reporting, polish CLI, comprehensive testing, documentation

**Deliverables:**
- ✅ CSV, JSON, HTML reporters
- ✅ Complete CLI với all commands
- ✅ Comprehensive documentation
- ✅ Example reports
- ✅ Final testing và bug fixes
- ✅ Release package

**Tasks:**

**Day 1-2 (T7-CN):**
- [ ] Implement `reporter/csv_reporter.py`
- [ ] Implement `reporter/json_reporter.py`
- [ ] Implement `reporter/html_reporter.py`:
  - Jinja2 templates
  - Interactive timeline
  - Charts (Chart.js)
  - Responsive design
- [ ] Test với large datasets

**Day 3-4 (T2-T3):**
- [ ] Complete CLI implementation:
  - `mfaa collect` command
  - `mfaa parse` command
  - `mfaa analyze` command (full pipeline)
  - `mfaa report` command
  - Help documentation
  - Man pages
- [ ] Add shell completions (bash, zsh)
- [ ] User experience testing

**Day 5 (T4):**
- [ ] Comprehensive testing:
  - End-to-end tests
  - Performance testing (benchmark large datasets)
  - Security testing
  - Cross-platform testing (macOS versions)
- [ ] Bug fixing

**Day 6 (T5):**
- [ ] Documentation:
  - Complete API documentation
  - User guide
  - Installation guide
  - Troubleshooting guide
  - Example use cases
- [ ] Code cleanup
- [ ] Final code review

**Day 7 (T6):**
- [ ] Package cho distribution:
  - Setup.py finalization
  - PyPI preparation
  - Create installers
- [ ] Final demo
- [ ] Release v1.0.0

**Week 4 Success Metrics:**
- ✅ All reporters functional
- ✅ CLI complete với excellent UX
- ✅ Documentation 100% complete
- ✅ All tests passing
- ✅ Ready for production use
- ✅ Package available for distribution

### 7.2 Gantt Chart

```
Week 1: Foundation & Research
├── [████████] Project Setup (Days 1-2)
├── [████████] Research FSEvents (Days 3-4)
├── [████████] Basic Parser (Days 5-6)
└── [████] Review (Day 7)

Week 2: Core Functionality
├── [████████] Collector Implementation (Days 1-2)
├── [████████] Parser v2 + Gzip (Days 3-4)
├── [████████] Xattr Extraction (Days 5-6)
└── [████] Integration Testing (Day 7)

Week 3: Analysis & Intelligence
├── [████████] Event Filtering (Days 1-2)
├── [████████] Scoring & Patterns (Days 3-4)
├── [████████] Timeline Generation (Days 5-6)
└── [████] CLI Basics (Day 7)

Week 4: Reporting & Finalization
├── [████████] Reporters (Days 1-2)
├── [████████] Complete CLI (Days 3-4)
├── [████] Testing (Day 5)
├── [████] Documentation (Day 6)
└── [████] Release (Day 7)
```

### 7.3 Milestones

| Milestone | Due Date | Deliverable | Success Criteria |
|-----------|----------|-------------|------------------|
| M1: Parser Prototype | 01/11 | FSEvents v1 parser working | Parse sample data successfully |
| M2: Collection Working | 08/11 | Can collect from live system | Collect + parse real macOS data |
| M3: Analysis Engine | 15/11 | Filtering + scoring functional | Generate priority timeline |
| M4: Beta Release | 22/11 | Complete tool ready | All features working, documented |

---

## 8. Test Strategy

### 8.1 Test Pyramid

```
                  ┌──────────────┐
                  │   E2E Tests  │  (10%)
                  │   ~~~~~~~~   │
                  └──────────────┘
              ┌────────────────────┐
              │ Integration Tests  │  (30%)
              │   ~~~~~~~~~~~~~~   │
              └────────────────────┘
          ┌──────────────────────────┐
          │      Unit Tests          │  (60%)
          │      ~~~~~~~~~~          │
          └──────────────────────────┘
```

### 8.2 Unit Tests (Target: 85% coverage)

**Test Coverage by Module:**

**Parser Tests:**
```python
# tests/test_fsevents_parser.py

def test_parse_v1_format():
    """Test parsing FSEvents version 1 format."""
    
def test_parse_v2_compressed():
    """Test parsing gzip compressed v2 format."""
    
def test_decode_flags():
    """Test flag decoding."""
    
def test_handle_malformed_data():
    """Test error handling với corrupt data."""
    
def test_unicode_paths():
    """Test Unicode path handling."""
    
def test_large_file_performance():
    """Test performance với large FSEvents file."""
```

**Collector Tests:**
```python
# tests/test_collector.py

def test_volume_scanner():
    """Test APFS volume detection."""
    
def test_fsevents_collection():
    """Test collecting FSEvents database."""
    
def test_hash_verification():
    """Test SHA-256 hash calculation."""
    
def test_permission_error_handling():
    """Test behavior khi không có permissions."""
```

**Analyzer Tests:**
```python
# tests/test_analyzer.py

def test_event_filtering():
    """Test various filter combinations."""
    
def test_priority_scoring():
    """Test scoring algorithm."""
    
def test_pattern_detection_ransomware():
    """Test ransomware pattern detection."""
    
def test_mass_deletion_detection():
    """Test mass deletion threshold."""
```

### 8.3 Integration Tests

```python
# tests/integration/test_full_pipeline.py

def test_collect_and_parse_pipeline():
    """Test full collection -> parsing pipeline."""
    # 1. Collect from test volume
    # 2. Parse collected data
    # 3. Verify results
    
def test_analyze_with_real_data():
    """Test analysis với real macOS data."""
    # Use sanitized real-world dataset
    
def test_report_generation():
    """Test generating all report formats."""
```

### 8.4 End-to-End Tests

```python
# tests/e2e/test_scenarios.py

def test_ransomware_investigation_scenario():
    """
    Scenario: Investigate suspected ransomware
    Steps:
    1. Collect artifacts
    2. Analyze with ransomware filters
    3. Generate report
    4. Verify suspicious events detected
    """
    
def test_insider_threat_scenario():
    """
    Scenario: Investigate data exfiltration
    """
    
def test_malware_download_scenario():
    """
    Scenario: Trace malware download and execution
    """
```

### 8.5 Performance Tests

```python
# tests/performance/test_benchmarks.py

def test_parsing_speed():
    """
    Requirement: ≥ 10,000 events/second
    Test with 1M events
    """
    
def test_memory_usage():
    """
    Requirement: ≤ 500MB for 1M events
    Monitor memory during parsing
    """
    
def test_large_dataset_handling():
    """
    Test với 10M+ events
    Verify no crashes, acceptable performance
    """
```

### 8.6 Test Data

**Test Data Requirements:**
- Sample FSEvents databases (v1 và v2)
- Files với various xattr combinations
- Simulated malware scenarios
- Large datasets cho performance testing

**Test Data Structure:**
```
tests/
└── fixtures/
    ├── fsevents/
    │   ├── v1_sample/
    │   ├── v2_compressed/
    │   └── corrupt_data/
    ├── xattr/
    │   ├── quarantine_samples/
    │   └── download_metadata/
    └── scenarios/
        ├── ransomware_simulation/
        ├── insider_threat/
        └── malware_download/
```

---

## 9. Security & Compliance

### 9.1 Security Considerations

**Data Handling:**
- ✅ Read-only operations trên source system
- ✅ No modification của original data
- ✅ Hash verification cho data integrity
- ✅ Secure storage của collected artifacts
- ✅ Sensitive data redaction options

**Access Control:**
- ⚠️ Requires root/administrator privileges
- ✅ Audit logging của tất cả operations
- ✅ Verified execution environment checks

**Data Privacy:**
- ✅ No cloud uploads without explicit user consent
- ✅ Local-only processing by default
- ✅ Configurable PII redaction
- ✅ Clear data retention policies

### 9.2 Compliance

**Forensics Standards:**
- ✅ Follow NIST SP 800-86 guidelines (digital forensics)
- ✅ Maintain chain of custody documentation
- ✅ Hash verification (SHA-256) for evidence integrity
- ✅ Timestamped audit logs
- ✅ Non-destructive acquisition methods

**Data Protection:**
- ✅ GDPR considerations cho EU users
- ✅ Options để anonymize PII trong reports
- ✅ Secure deletion của temporary files

### 9.3 Security Testing

```python
# tests/security/test_security.py

def test_no_data_modification():
    """Verify tool doesn't modify source data."""
    
def test_privilege_escalation():
    """Ensure no unintended privilege escalation."""
    
def test_injection_attacks():
    """Test resistance to path injection, etc."""
    
def test_sensitive_data_handling():
    """Verify proper handling of passwords, keys, etc."""
```

---

## 10. Deliverables

### 10.1 Code Deliverables

**Week 4 Final Package:**
```
mfaa-1.0.0/
├── mfaa/                      # Source code
│   ├── __init__.py
│   ├── cli.py
│   ├── collector/
│   ├── parser/
│   ├── analyzer/
│   ├── timeline/
│   ├── reporter/
│   └── utils/
├── tests/                     # Comprehensive test suite
├── docs/                      # Documentation
│   ├── API.md
│   ├── UserGuide.md
│   ├── DeveloperGuide.md
│   └── FSEventsFormat.md
├── examples/                  # Example scripts và configs
│   ├── config/
│   │   ├── filters.yaml
│   │   └── scoring.yaml
│   ├── reports/              # Sample reports
│   └── scenarios/            # Example use cases
├── requirements.txt
├── setup.py
├── README.md
├── LICENSE
├── CHANGELOG.md
└── .github/
    └── workflows/
        └── ci.yml
```

### 10.2 Documentation Deliverables

1. **Technical Specification** (this document)
2. **API Documentation** - Complete API reference
3. **User Guide** - Step-by-step usage instructions
4. **Developer Guide** - For contributors
5. **FSEvents Format Documentation** - Research findings
6. **Installation Guide** - Setup instructions
7. **Troubleshooting Guide** - Common issues và solutions

### 10.3 Testing Deliverables

1. **Test Suite** - Complete automated tests
2. **Test Report** - Coverage và results
3. **Performance Benchmarks** - Speed và memory metrics
4. **Test Data Sets** - Sanitized sample data

### 10.4 Reporting Examples

**Sample Reports Package:**
- CSV export example
- JSON export example
- HTML interactive report example
- Executive summary example
- Incident report template

---

## 11. Dependencies

### 11.1 Python Dependencies

```txt
# requirements.txt

# Core dependencies
click>=8.1.0           # CLI framework
pyyaml>=6.0            # Config file parsing
jinja2>=3.1.0          # HTML template engine

# Optional dependencies
colorama>=0.4.6        # Cross-platform colored terminal
tqdm>=4.65.0           # Progress bars
tabulate>=0.9.0        # Table formatting

# Development dependencies (requirements-dev.txt)
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.7.0
flake8>=6.1.0
mypy>=1.5.0
sphinx>=7.1.0          # Documentation
```

### 11.2 System Requirements

**Minimum:**
- macOS 10.13 (High Sierra) or later
- Python 3.9+
- 500MB RAM
- 1GB free disk space
- Administrator/root privileges

**Recommended:**
- macOS 12+ (Monterey or later)
- Python 3.11+
- 2GB RAM
- 5GB free disk space
- SSD for faster processing

**Supported Architectures:**
- Intel x86_64
- Apple Silicon (M1/M2/M3)

---

## 12. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| FSEvents format changes in future macOS | High | Medium | Version detection, graceful fallback, regular updates |
| Performance issues với very large datasets | Medium | Medium | Streaming parsing, batch processing, optimization |
| Permission issues on target system | High | High | Clear error messages, permission check upfront |
| False positives trong pattern detection | Medium | Medium | Tunable thresholds, manual review capability |
| Time constraint (4 weeks) | Medium | Low | Prioritize must-have features, defer nice-to-haves |

---

## 13. Success Criteria

**Technical Criteria:**
- ✅ Parse FSEvents với ≥99.5% accuracy
- ✅ Process ≥10,000 events/second
- ✅ Memory usage ≤500MB for 1M events
- ✅ Test coverage ≥85%
- ✅ Support macOS 10.13 to macOS 15

**Functional Criteria:**
- ✅ Successfully collect artifacts từ live macOS
- ✅ Generate actionable priority timeline
- ✅ Detect ransomware patterns trong test scenarios
- ✅ Export reports trong CSV/JSON/HTML

**Quality Criteria:**
- ✅ Zero crashes trên valid input
- ✅ Graceful error handling
- ✅ Clear, comprehensive documentation
- ✅ Easy to use CLI

**User Acceptance:**
- ✅ Reduces manual analysis time by ≥80%
- ✅ Positive feedback from pilot users
- ✅ Successfully used trong real investigation

---

## 14. Appendices

### Appendix A: FSEvents Format Reference

```
FSEvents File Structure (Simplified)

┌─────────────────────────────────────┐
│         Page Header (8 bytes)       │
├─────────────────────────────────────┤
│  - Signature: "1SLD" or "2SLD"      │
│  - Unknown fields                   │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│      Records (variable length)      │
├─────────────────────────────────────┤
│  Each record:                       │
│  - Path (null-terminated string)    │
│  - Event ID (8 bytes)               │
│  - Flags (4 bytes)                  │
│  - (optional) Node ID               │
└─────────────────────────────────────┘

Version 2 (DLS): Gzip compressed
```

### Appendix B: Quarantine Flags Reference

```
com.apple.quarantine format:
"XXXX;TIMESTAMP;APP;UUID"

Flags (XXXX):
- 0000: Unknown/Other
- 0001: Web download
- 0002: Saved from unknown source
- 0003: Saved from safe source

Examples:
"0083;673a8f2d;Safari;F643CD5F-..."
  └─ Web download via Safari
```

### Appendix C: Example CLI Usage

```bash
# Basic analysis
$ sudo mfaa analyze --output-dir /case/evidence

# Custom filtering
$ sudo mfaa analyze \
    --filter-config my_filters.yaml \
    --time-range "2025-10-01" "2025-10-26" \
    --format html

# Collect only
$ sudo mfaa collect --volume "/Volumes/MacHD" \
    --output-dir /external/collection

# Parse already collected data
$ mfaa parse /external/collection/fsevents \
    --output /external/parsed.json

# Generate report from parsed data
$ mfaa report /external/parsed.json \
    --format html \
    --output report.html
```

### Appendix D: Sample Config Files

*(Already covered in Section 5.3)*

### Appendix E: References

**Technical References:**
1. Apple FSEvents API Documentation
2. APFS File System Reference
3. macOS Extended Attributes Guide
4. NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response

**Tools & Libraries:**
1. mac_apt - macOS Artifact Parsing Tool
2. FSEventsParser - Python library for FSEvents
3. pyxattr - Python extended attributes module

**Academic Papers:**
1. "Digital Forensics of Apple Desktops" - Various authors
2. "Analyzing FSEvents on macOS" - Research papers
3. "APFS Forensics" - Security research

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-26 | Digital Forensics Team | Initial specification document |

---

## Approval

**Document Status:** Draft - Awaiting Approval

**Prepared By:** Digital Forensics & Business Analysis Team  
**Date:** 26/10/2025

**To Be Reviewed By:**
- [ ] Technical Lead
- [ ] Security Officer
- [ ] Project Manager
- [ ] Legal/Compliance Team

---

*End of Specification Document*