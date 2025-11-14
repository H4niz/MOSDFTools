# Getting Started with mFAA

**mFAA (macOS Forensics Artifacts Analyzer)** is a comprehensive digital forensics tool designed for live acquisition and analysis of macOS file system artifacts.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Basic Workflow](#basic-workflow)
5. [Next Steps](#next-steps)

---

## System Requirements

### Operating System
- **macOS 10.13 (High Sierra)** or later
- **Apple Silicon (M1/M2/M3)** or Intel-based Mac
- **APFS file system** (default on modern macOS)

### Software Requirements
- **Python 3.9+**
- **pip** (Python package manager)
- **Root/Administrator privileges** (for FSEvents collection)

### Hardware Requirements
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 500MB for installation, additional space for analysis output
- **Disk:** SSD recommended for performance

### Optional Requirements
- **Docker** (for containerized deployment)
- **Git** (for source installation)

---

## Installation

### Method 1: From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/mfaa.git
cd mfaa

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install mFAA in development mode
pip install -e .

# Verify installation
mfaa --version
```

### Method 2: Using pip (Production)

```bash
# Install from PyPI (once published)
pip install mfaa

# Verify installation
mfaa --version
```

### Method 3: Using Docker

```bash
# Pull the Docker image
docker pull mfaa:latest

# Run mFAA in container
docker run -it --privileged -v /:/host mfaa:latest

# Or build from source
docker build -f Dockerfile.prod -t mfaa:prod .
docker run -it --privileged -v /:/host mfaa:prod
```

---

## Quick Start

### 1. Basic Collection and Analysis

Collect FSEvents from the root volume and generate a timeline:

```bash
# Full analysis (requires root)
sudo mfaa analyze --volume / --output ./analysis --format html

# This performs:
# 1. FSEvents collection
# 2. Parsing
# 3. Priority scoring
# 4. Timeline generation
# 5. HTML report creation
```

### 2. View the Report

```bash
# Open the generated HTML report
open ./analysis/timeline_report.html
```

### 3. Generate Multiple Formats

```bash
# Generate all report formats
sudo mfaa analyze --volume / --output ./analysis --format all

# This creates:
# - timeline_report.csv
# - timeline_report.json
# - timeline_report.html
# - executive_summary.html
```

---

## Basic Workflow

### Step 1: Collection

Collect FSEvents and extended attributes from a volume:

```bash
# Collect from root volume
sudo mfaa collect --volume / --output ./evidence

# Collect from external volume
sudo mfaa collect --volume /Volumes/External --output ./evidence

# Collect without extended attributes (faster)
sudo mfaa collect --volume / --output ./evidence --no-xattr
```

**Output Structure:**
```
evidence/
├── Macintosh_HD/
│   ├── .fseventsd/
│   │   ├── 0000000000abcdef
│   │   └── ...
│   ├── acquisition_log.json
│   └── xattr_records.json
```

### Step 2: Parsing

Parse collected FSEvents files:

```bash
# Parse single file
mfaa parse ./evidence/Macintosh_HD/.fseventsd/0000000000abcdef \
    --output ./parsed_events.json

# Parse entire directory
mfaa parse ./evidence/Macintosh_HD/.fseventsd/ \
    --output ./parsed_events.json

# Use compact format (smaller file size)
mfaa parse ./evidence/Macintosh_HD/.fseventsd/ \
    --output ./parsed_events.json \
    --format json-compact
```

### Step 3: Analysis & Reporting

Generate timeline and reports from parsed events:

```bash
# Generate HTML report
mfaa report ./parsed_events.json \
    --format html \
    --output ./reports/

# Generate CSV for spreadsheet analysis
mfaa report ./parsed_events.json \
    --format csv \
    --output ./reports/

# Generate JSON for programmatic access
mfaa report ./parsed_events.json \
    --format json \
    --output ./reports/

# Generate executive summary
mfaa report ./parsed_events.json \
    --format executive \
    --output ./reports/
```

---

## Understanding the Output

### HTML Report Structure

The interactive HTML report includes:

1. **Executive Summary**
   - Total events analyzed
   - Priority distribution (Critical, High, Medium, Low)
   - Suspicious patterns detected
   - Time range covered

2. **Timeline View**
   - Interactive timeline with zoom/pan
   - Filterable by priority, event type, path
   - Searchable event details

3. **Pattern Analysis**
   - Detected threat patterns (ransomware, exfiltration, etc.)
   - Severity scoring
   - Related events grouped

4. **Statistics Dashboard**
   - Event type distribution
   - File type analysis
   - Temporal distribution
   - Hot paths (most active directories)

### CSV Report Format

```csv
timestamp,event_id,path,event_types,priority_score,priority_category,notes
2024-01-15T10:00:00,1,/Users/test/document.txt,"Created,IsFile",75,HIGH,"Downloaded file with quarantine"
```

### JSON Report Structure

```json
{
  "timeline": {
    "entries": [...],
    "patterns": [...],
    "statistics": {...}
  },
  "metadata": {
    "generated_at": "2024-01-15T10:00:00",
    "tool_version": "1.0.0",
    "total_events": 1000
  }
}
```

---

## Common Use Cases

### Use Case 1: Incident Response

```bash
# Quick triage of recent activity
sudo mfaa analyze \
    --volume / \
    --output ./incident_$(date +%Y%m%d) \
    --format html \
    --open-browser
```

### Use Case 2: Malware Analysis

```bash
# Focus on suspicious paths
sudo mfaa analyze \
    --volume / \
    --output ./malware_analysis \
    --format all

# Review the timeline for:
# - /tmp/ activity
# - LaunchAgents/LaunchDaemons creation
# - Application installations
# - Script executions
```

### Use Case 3: Data Exfiltration Investigation

```bash
# Analyze for data exfiltration patterns
sudo mfaa analyze \
    --volume / \
    --output ./exfiltration_check \
    --format html

# Look for:
# - Large file movements to external volumes
# - Compressed archives created in Downloads
# - Network share access
```

### Use Case 4: User Activity Reconstruction

```bash
# Timeline of user's desktop activity
sudo mfaa collect --volume / --output ./evidence
mfaa parse ./evidence/Macintosh_HD/.fseventsd/ --output ./events.json
mfaa report ./events.json --format html --output ./user_activity/
```

---

## Next Steps

- **[Command Reference](command-reference.md)** - Complete CLI command documentation
- **[Configuration Guide](../configuration/configuration-guide.md)** - Customize scoring weights and detection patterns
- **[Advanced Usage](advanced-usage.md)** - Timeline filtering, custom scripts, API usage
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

---

## Getting Help

- **Documentation:** [Full Documentation](../README.md)
- **Issues:** [GitHub Issues](https://github.com/yourusername/mfaa/issues)
- **Community:** [Discussions](https://github.com/yourusername/mfaa/discussions)

---

**Version:** 1.0.0
**Last Updated:** 2025-10-26
