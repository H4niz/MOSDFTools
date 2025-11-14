# mFAA User Guide
## macOS Forensics Artifacts Analyzer - Complete Usage Guide

**Version:** 1.0+ with FSEvents v3 Support
**Last Updated:** November 2, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Command Reference](#command-reference)
4. [Workflow Examples](#workflow-examples)
5. [Understanding Reports](#understanding-reports)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)
8. [FAQ](#faq)

---

## Quick Start

### Fastest Way to Get Started

```bash
# 1. Clone and install
git clone https://github.com/yourusername/mfaa.git
cd mfaa
pip3 install -r requirements.txt

# 2. Generate forensic report (uses existing test data if available)
python3 scripts/generate_forensic_report.py

# 3. View results
open output/forensic_reports/forensic_analysis.html
```

### Full Analysis (Requires sudo)

```bash
# Collect and analyze your system
sudo python3 -m mfaa.cli analyze --volume / --output ./my_analysis --format html

# View the report
open ./my_analysis/forensic_analysis.html
```

---

## Installation

### System Requirements

- **Operating System:** macOS 10.13 (High Sierra) or later
  - ✅ Tested on macOS Sequoia 15.6.1
  - ✅ Supports Apple Silicon and Intel Macs
- **Python:** Version 3.9 or higher
- **Disk Space:** ~500 MB for reports (varies with event count)
- **Privileges:** Sudo/root access for FSEvents collection

### Step-by-Step Installation

#### 1. Install Python 3.9+ (if needed)

```bash
# Check current version
python3 --version

# If < 3.9, install via Homebrew
brew install python@3.9
```

#### 2. Clone Repository

```bash
git clone https://github.com/yourusername/mfaa.git
cd mfaa
```

#### 3. Install Dependencies

```bash
# Install required packages
pip3 install -r requirements.txt

# Verify installation
python3 -c "from mfaa.parser.fsevents_parser import FSEventsParser; print('✓ mFAA installed successfully')"
```

#### 4. (Optional) Set up Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Command Reference

### Command Structure

```
python3 -m mfaa.cli <command> [options]
```

### Available Commands

| Command | Purpose | Requires Sudo |
|---------|---------|---------------|
| `gather` | Scan for available artifacts | ❌ No |
| `collect` | Collect FSEvents and artifacts | ✅ Yes |
| `parse_cmd` | Parse collected FSEvents | ❌ No |
| `analyze` | Full analysis pipeline | ✅ Yes (for collection) |
| `report_cmd` | Generate reports from data | ❌ No |

---

### 1. `gather` - Scan for Artifacts

**Purpose:** Survey what forensic artifacts are available on the system without collecting them.

**Syntax:**
```bash
python3 -m mfaa.cli gather --volume <path> --output <file>
```

**Options:**
- `--volume` - Volume to scan (default: `/`)
- `--output` - JSON file to save results

**Example:**
```bash
python3 -m mfaa.cli gather --volume / --output artifact_scan.json
```

**Output:** JSON file listing:
- Available artifact types
- Accessibility status
- Collection commands needed

---

### 2. `collect` - Collect Forensic Data

**Purpose:** Collect FSEvents databases and extended attributes from a volume.

**Syntax:**
```bash
sudo python3 -m mfaa.cli collect --volume <path> --output-dir <dir>
```

**Options:**
- `--volume` - Volume to collect from (default: `/`)
- `--output-dir` - Directory to store collected data
- `--verify-hashes` - Calculate SHA-256 checksums (default: enabled)

**Example:**
```bash
sudo python3 -m mfaa.cli collect --volume / --output-dir ./collected_data
```

**Output:**
- FSEvents database files in `<output-dir>/<volume>/.fseventsd/`
- SHA-256 checksums in `<output-dir>/checksums.txt`
- Collection log with chain of custody info

---

### 3. `parse_cmd` - Parse FSEvents

**Purpose:** Parse FSEvents binary files into structured JSON format.

**Syntax:**
```bash
python3 -m mfaa.cli parse_cmd <fsevents_dir> --output <file>
```

**Options:**
- `<fsevents_dir>` - Path to `.fseventsd` directory
- `--output` - JSON file to save parsed events
- `--version` - Force specific FSEvents version (1, 2, or 3)

**Example:**
```bash
python3 -m mfaa.cli parse_cmd ./collected_data/.fseventsd --output parsed_events.json
```

**Auto-Detection:**
- Automatically detects v1/v2/v3 formats
- No `--version` parameter needed in most cases

---

### 4. `analyze` - Full Analysis Pipeline

**Purpose:** Complete forensic analysis: collect → parse → analyze → report.

**Syntax:**
```bash
sudo python3 -m mfaa.cli analyze [options]
```

**Options:**
- `--volume <path>` - Volume to analyze (default: `/`)
- `--output <dir>` - Output directory for reports
- `--format <fmt>` - Report format: `csv`, `json`, `html`, or `all`
- `--min-priority <n>` - Filter events with priority ≥ n (0-100)
- `--time-range <start> <end>` - Filter by date (YYYY-MM-DD format)
- `--skip-collection` - Use existing data (no sudo needed)
- `--input <file>` - Parsed JSON file (with `--skip-collection`)

**Examples:**

Full analysis:
```bash
sudo python3 -m mfaa.cli analyze --volume / --output ./analysis --format html
```

High-priority events only:
```bash
sudo python3 -m mfaa.cli analyze --output ./critical --min-priority 70 --format all
```

Use existing data (no sudo):
```bash
python3 -m mfaa.cli analyze --skip-collection --input parsed.json --output ./reports
```

Time range filter:
```bash
sudo python3 -m mfaa.cli analyze --output ./analysis \
  --time-range "2025-11-01" "2025-11-02" --format html
```

---

### 5. `report_cmd` - Generate Reports

**Purpose:** Create forensic reports from already-parsed event data.

**Syntax:**
```bash
python3 -m mfaa.cli report_cmd <parsed_json> [options]
```

**Options:**
- `<parsed_json>` - Path to parsed events JSON file
- `--format <fmt>` - Report format: `csv`, `json`, or `html`
- `--output <dir>` - Output directory

**Example:**
```bash
python3 -m mfaa.cli report_cmd parsed_events.json --format html --output ./reports
```

---

## Workflow Examples

### Scenario 1: Quick Security Check

**Goal:** Quick triage of recent system activity

```bash
# Step 1: Generate report from existing data
python3 scripts/generate_forensic_report.py

# Step 2: Open executive summary
open output/forensic_reports/executive_summary.html

# Step 3: Check for critical patterns
grep "CRITICAL" output/forensic_reports/forensic_analysis.csv
```

**Time:** ~2-5 minutes
**Sudo:** Not required

---

### Scenario 2: Full Forensic Investigation

**Goal:** Complete forensic analysis with all artifacts

```bash
# Step 1: Survey available artifacts
python3 -m mfaa.cli gather --volume / --output scan.json

# Step 2: Collect FSEvents
sudo python3 -m mfaa.cli collect --volume / --output-dir ./evidence

# Step 3: Parse events
python3 -m mfaa.cli parse_cmd ./evidence/.fseventsd --output events.json

# Step 4: Analyze and generate reports
python3 -m mfaa.cli analyze --skip-collection --input events.json \
  --output ./reports --format all

# Step 5: Review results
open ./reports/forensic_analysis.html
open ./reports/executive_summary.html
```

**Time:** ~15-30 minutes (depending on event count)
**Sudo:** Required for Step 2

---

### Scenario 3: Incident Response (Specific Time Window)

**Goal:** Analyze activity during a suspected incident

```bash
# Analyze events from November 1-2, 2025
sudo python3 -m mfaa.cli analyze --volume / --output ./incident_20251101 \
  --time-range "2025-11-01" "2025-11-02" \
  --format html

# Filter for high-priority events
grep -E "HIGH|CRITICAL" ./incident_20251101/forensic_analysis.csv > critical_events.csv

# Open report
open ./incident_20251101/forensic_analysis.html
```

**Time:** ~10-20 minutes
**Sudo:** Required

---

### Scenario 4: Malware Analysis

**Goal:** Track specific suspicious file activity

```bash
# Step 1: Collect data
sudo python3 -m mfaa.cli analyze --volume / --output ./malware_check

# Step 2: Search for suspicious paths
grep -i "suspicious_app" ./malware_check/forensic_analysis.csv

# Step 3: Filter executables only
grep "\.app\|\.dmg\|\.pkg" ./malware_check/forensic_analysis.csv

# Step 4: Check quarantine flags
grep "has_quarantine.*true" ./malware_check/forensic_analysis.json
```

---

## Understanding Reports

### Report Types

#### 1. HTML Report (`forensic_analysis.html`)

**Features:**
- Interactive timeline table
- Real-time filtering and search
- Sortable columns
- Event type visualization
- Priority distribution charts

**How to Use:**
1. Open in web browser
2. Use search box to find specific files/paths
3. Click column headers to sort
4. Use priority filter to focus on critical events
5. Export filtered results if needed

**Best For:** Interactive investigation and exploration

---

#### 2. Executive Summary (`executive_summary.html`)

**Features:**
- High-level overview
- Pattern detection results
- Priority statistics
- Security assessment

**Contents:**
- Analysis metadata (date, events count, etc.)
- Top critical events
- Detected patterns summary
- Recommendations

**Best For:** Management reports and quick assessment

---

#### 3. JSON Report (`forensic_analysis.json`)

**Features:**
- Machine-readable format
- Complete event data
- Programmatic access

**Structure:**
```json
{
  "analysis_metadata": {...},
  "timeline_entries": [
    {
      "event_id": 12345,
      "timestamp": "1970-01-01T00:00:00",
      "path": "Library/...",
      "flags": {...},
      "priority_score": 45,
      "priority_category": "MEDIUM"
    }
  ],
  "patterns": [...],
  "statistics": {...}
}
```

**Best For:** Automation, SIEM integration, custom analysis

---

#### 4. CSV Report (`forensic_analysis.csv`)

**Features:**
- Spreadsheet-compatible
- Easy filtering in Excel/LibreOffice
- Simple text processing

**Columns:**
- Event ID
- Timestamp
- Path
- Event Types
- Priority Score
- Priority Category
- Has Quarantine
- Is Downloaded
- Node ID

**Best For:** Spreadsheet analysis, pivot tables, custom filtering

---

### Priority Categories

| Category | Score Range | Meaning | Action |
|----------|-------------|---------|--------|
| **CRITICAL** | 80-100 | High-risk activity detected | Immediate investigation |
| **HIGH** | 60-79 | Suspicious behavior | Review promptly |
| **MEDIUM** | 40-59 | Noteworthy activity | Monitor |
| **LOW** | 0-39 | Normal operations | Routine review |

---

### Pattern Detection

mFAA detects 5 types of suspicious patterns:

#### 1. Mass Deletion
**Indicator:** >50 files deleted in <60 seconds
**Possible Cause:** Ransomware, data destruction
**Action:** Investigate deleted file paths

#### 2. Ransomware Activity
**Indicators:**
- Files renamed to `.encrypted`, `.locked`, `.crypto`
- Creation of ransom notes (`.txt`, `.html`)
**Action:** Check for encryption signatures

#### 3. Data Exfiltration
**Indicators:**
- Large files copied to external volumes
- Archive creation (`.zip`, `.tar.gz`, `.7z`)
**Action:** Review file destinations

#### 4. Persistence Mechanisms
**Indicators:**
- LaunchAgents/LaunchDaemons created
- Shell profile modifications
**Action:** Examine startup items

#### 5. Credential Access
**Indicators:**
- Access to keychain files
- Browser credential databases
**Action:** Check for unauthorized access

---

## Troubleshooting

### Common Issues

#### Issue 1: "Permission denied" on FSEvents

**Error:**
```
Permission denied: /.fseventsd
```

**Solution:**
```bash
# Run with sudo
sudo python3 -m mfaa.cli analyze --volume / --output ./analysis
```

---

#### Issue 2: "FSEvents directory not found"

**Error:**
```
FSEvents directory not found: /.fseventsd
```

**Solution (macOS Catalina+):**
```bash
# Use the correct path
sudo python3 -m mfaa.cli collect --volume / --output-dir ./collected

# The tool should auto-detect /System/Volumes/Data/.fseventsd
# If not, check: ls -la /System/Volumes/Data/.fseventsd
```

---

#### Issue 3: "No events parsed!"

**Possible Causes:**
1. FSEvents files are empty
2. Permission issues
3. Corrupted files

**Solution:**
```bash
# Check file permissions
ls -la output/collected/.fseventsd/

# Fix permissions if needed
sudo chmod 644 output/collected/.fseventsd/*

# Try parsing again
python3 -m mfaa.cli parse_cmd output/collected/.fseventsd --output test.json
```

---

#### Issue 4: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'mfaa'
```

**Solution:**
```bash
# Option 1: Run from project root
cd /path/to/MOSDFTools
python3 -m mfaa.cli analyze --help

# Option 2: Set PYTHONPATH
export PYTHONPATH=/path/to/MOSDFTools
python3 scripts/generate_forensic_report.py

# Option 3: Install in development mode
pip3 install -e .
```

---

### Debug Mode

Enable verbose logging:

```bash
# Set logging level
export MFAA_LOG_LEVEL=DEBUG

# Run command
python3 -m mfaa.cli analyze --volume / --output ./debug_analysis
```

Check logs in:
- Console output
- `<output_dir>/analysis.log`

---

## Advanced Usage

### Custom Filtering

Create `my_filters.yaml`:

```yaml
event_types:
  - ITEM_CREATED
  - ITEM_REMOVED
  - ITEM_MODIFIED

paths:
  include:
    - "^/Applications/"
    - "^/Users/.*/Downloads/"
  exclude:
    - "^/System/"
    - "\\.log$"

extensions:
  executables: [".app", ".dmg", ".pkg"]
  documents: [".pdf", ".docx", ".xlsx"]

min_priority: 50

time_range:
  start: "2025-11-01 00:00:00"
  end: "2025-11-02 23:59:59"
```

Use custom filters:

```bash
python3 -m mfaa.cli analyze --output ./custom \
  --filter-config my_filters.yaml --format html
```

---

### Analyzing Multiple Volumes

```bash
# List all volumes
diskutil list

# Collect from external drive
sudo python3 -m mfaa.cli collect \
  --volume "/Volumes/External HD" \
  --output-dir ./external_analysis
```

---

### Batch Processing

Process multiple systems:

```bash
#!/bin/bash
# analyze_batch.sh

SYSTEMS=("system1" "system2" "system3")

for sys in "${SYSTEMS[@]}"; do
  echo "Analyzing $sys..."
  python3 -m mfaa.cli analyze \
    --skip-collection \
    --input "data/${sys}_events.json" \
    --output "reports/${sys}" \
    --format all
done
```

---

### Exporting to SIEM

Export JSON for Splunk/ELK:

```bash
# Generate JSON report
python3 -m mfaa.cli analyze --skip-collection \
  --input events.json --output ./siem --format json

# Upload to SIEM
curl -X POST http://splunk-server:8088/services/collector \
  -H "Authorization: Splunk <token>" \
  -d @./siem/forensic_analysis.json
```

---

## FAQ

### General Questions

**Q: Does mFAA modify any system files?**
A: No. mFAA operates in read-only mode. All collection uses copy operations, never moves or deletes files.

**Q: Can I run mFAA on a live production system?**
A: Yes. mFAA is designed for live acquisition with minimal system impact.

**Q: How long does analysis take?**
A: Varies by event count:
- 100K events: ~2-5 minutes
- 1M events: ~10-20 minutes
- 5M+ events: ~30-60 minutes

**Q: What's the difference between v1, v2, and v3 FSEvents?**
A:
- **v1:** Uncompressed (macOS 10.5-10.12)
- **v2:** Gzip-compressed (macOS 10.13-14.x)
- **v3:** New format (macOS 15.x Sequoia)
- mFAA auto-detects all three

---

### Technical Questions

**Q: Why don't v3 events have timestamps?**
A: FSEvents v3 format doesn't include timestamps in individual records. Events are ordered by Event ID. Use file modification times as a reference.

**Q: What are the "unknown flag" warnings?**
A: v3 uses different flag combinations than v1/v2. Events are still captured, but some flags aren't yet mapped to event types. This doesn't affect analysis.

**Q: Can I analyze FSEvents from a disk image?**
A: Yes. Mount the image and point mFAA to the mount point:
```bash
hdiutil attach disk.dmg
python3 -m mfaa.cli collect --volume "/Volumes/Mounted Image"
```

**Q: How do I reduce report size?**
A: Use priority filtering:
```bash
python3 -m mfaa.cli analyze --min-priority 40 --output ./filtered
```

---

### Troubleshooting Questions

**Q: Why is my HTML report so large?**
A: HTML reports include all event data for interactivity. For 100K events, expect ~100-150 MB. Use CSV/JSON for smaller files.

**Q: Can I resume a stopped analysis?**
A: If collection completed, yes:
```bash
python3 -m mfaa.cli analyze --skip-collection \
  --input ./collected/events.json --output ./analysis
```

**Q: How do I verify mFAA collected files correctly?**
A: Check SHA-256 hashes:
```bash
cat ./collected/checksums.txt
shasum -a 256 ./collected/.fseventsd/* | diff - ./collected/checksums.txt
```

---

## Getting Help

### Resources

- **README:** [README.md](../README.md)
- **Technical Docs:** `docs/` directory
- **Change Logs:** `changes_logs/` directory
- **Example Reports:** `output/forensic_reports/`

### Support

- **GitHub Issues:** Report bugs and request features
- **GitHub Discussions:** Ask questions and share tips
- **Documentation:** This guide + inline help (`--help`)

### Command Help

Get help on any command:

```bash
python3 -m mfaa.cli --help
python3 -m mfaa.cli analyze --help
python3 -m mfaa.cli collect --help
```

---

## Summary

This guide covered:

✅ Installation and setup
✅ All CLI commands
✅ Common workflows
✅ Report interpretation
✅ Troubleshooting
✅ Advanced techniques

**Next Steps:**
1. Run `python3 scripts/generate_forensic_report.py` to test
2. Review the generated HTML report
3. Try a full analysis on your system
4. Customize filters for your use case

Happy investigating! 🔍
