# Practical Tutorial: Analyzing Your Documents Folder

**Level:** Beginner
**Time:** 15 minutes
**Prerequisites:** mFAA installed, macOS 10.13+

This tutorial walks you through a real-world analysis of your Documents folder to demonstrate mFAA's capabilities.

---

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [Step-by-Step Walkthrough](#step-by-step-walkthrough)
4. [Understanding the Results](#understanding-the-results)
5. [Advanced Analysis](#advanced-analysis)
6. [Troubleshooting](#troubleshooting)

---

## Overview

### What You'll Learn

- How to collect FSEvents from a specific directory
- How to parse and analyze file system events
- How to generate interactive HTML reports
- How to interpret analysis results

### What You'll Analyze

We'll analyze the `~/Documents` folder to discover:
- Recently created/modified files
- Downloaded documents
- Suspicious file operations
- Timeline of document activity

### Expected Output

```
demo_output/
├── artifacts/          # Collected FSEvents
├── parsed_events.json  # Parsed FSEvents data
└── reports/            # HTML/CSV/JSON reports
    ├── timeline_report.html
    ├── timeline_report.csv
    └── timeline_report.json
```

---

## Setup

### 1. Verify Installation

```bash
# Activate virtual environment
cd /Users/anhnlq/Documents/GitHub/MOSDFTools
source .venv/bin/activate

# Check mFAA version
python3 -m mfaa.cli.main --version

# Expected output:
# mFAA version 1.0.0
```

### 2. Create Working Directory

```bash
# Create directory for tutorial outputs
mkdir -p ~/mfaa_tutorial
cd ~/mfaa_tutorial

# Create subdirectories
mkdir -p artifacts parsed reports
```

### 3. Verify Permissions

**Note:** FSEvents collection requires root privileges. You'll need to use `sudo` for the collection step.

```bash
# Check if you can access FSEvents directory
ls -la /.fseventsd/

# If you see "Permission denied", you'll need sudo
```

---

## Step-by-Step Walkthrough

### Step 1: Collect FSEvents (Requires sudo)

**What it does:** Collects the FSEvents database from your system, which contains records of all file system activity.

```bash
# Navigate to working directory
cd ~/mfaa_tutorial

# Collect FSEvents from root volume (includes Documents folder events)
# Note: We collect from root (/) because FSEvents are stored at volume level
sudo python3 -m mfaa.cli.main collect \
    --output ./artifacts \
    --include-xattr \
    --verify-hashes

# You'll be prompted for your password
```

**Expected output:**
```
🔍 FSEvents Collector - mFAA v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Volume: /
📂 Output: ./artifacts

⚙️  Settings:
   • Include xattr: Yes
   • Verify hashes: Yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scanning volume...  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✓ Collected 42 FSEvents files (2.3 MB)
✓ Collected 1,234 xattr records
✓ Generated SHA-256 hashes
✓ Created acquisition log

📊 Collection Summary:
   • Files collected: 42
   • Total size: 2.3 MB
   • Duration: 45 seconds
   • Output: ./artifacts/Macintosh_HD/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Collection complete!
```

**What just happened:**
- mFAA copied FSEvents database files from `/.fseventsd/`
- Collected extended attributes (quarantine info, download sources)
- Calculated SHA-256 hashes for forensic integrity
- Created an acquisition log with metadata

**Verify the collection:**
```bash
ls -lh ./artifacts/Macintosh_HD/

# Expected output:
# drwxr-xr-x  .fseventsd/
# -rw-r--r--  acquisition_log.json
# -rw-r--r--  xattr_records.json
```

---

### Step 2: Parse FSEvents (No sudo needed)

**What it does:** Converts binary FSEvents files into human-readable JSON format.

```bash
# Parse the collected FSEvents
python3 -m mfaa.cli.main parse \
    ./artifacts/Macintosh_HD/.fseventsd/ \
    --output ./parsed/events.json \
    --format json

# This processes all FSEvents files in the directory
```

**Expected output:**
```
🔧 FSEvents Parser - mFAA v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Input: ./artifacts/Macintosh_HD/.fseventsd/
📄 Output: ./parsed/events.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Parsing FSEvents files...
  0000000000abcdef  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%  (1,234 events)
  0000000000fedcba  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%  (987 events)
  ... (40 more files)

✓ Parsed 45,678 events
✓ Time range: 2025-09-01 to 2025-10-26
✓ Output: ./parsed/events.json (8.5 MB)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Parsing complete!
```

**What just happened:**
- mFAA read all binary FSEvents files (v1 and v2/DLS formats)
- Decoded event types, paths, timestamps, and flags
- Saved as structured JSON for analysis

**Inspect the parsed data:**
```bash
# View first few events
head -n 50 ./parsed/events.json

# Count total events
grep -c "event_id" ./parsed/events.json
```

---

### Step 3: Generate Reports (No sudo needed)

**What it does:** Creates timeline analysis with priority scoring and pattern detection.

#### 3.1 Generate HTML Report (Interactive)

```bash
# Create interactive HTML report
python3 -m mfaa.cli.main report \
    ./parsed/events.json \
    --format html \
    --output ./reports/timeline.html \
    --theme light

# For dark theme users:
# --theme dark
```

**Expected output:**
```
📊 Report Generator - mFAA v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 Input: ./parsed/events.json
📄 Format: HTML
🎨 Theme: light

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Loading events...          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
Calculating priorities...  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
Detecting patterns...      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
Generating timeline...     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
Rendering HTML...          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

📊 Analysis Summary:
   • Total events: 45,678
   • High priority: 1,234 (2.7%)
   • Medium priority: 5,678 (12.4%)
   • Low priority: 38,766 (84.9%)
   • Patterns detected: 3
     - Data Exfiltration: 1 instance
     - Suspicious Execution: 2 instances

✓ Report generated: ./reports/timeline.html (2.1 MB)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Report generation complete!
```

**Open the report:**
```bash
# Open in default browser
open ./reports/timeline.html

# Or manually navigate to the file
```

#### 3.2 Generate CSV Report (Spreadsheet Analysis)

```bash
# Generate CSV for Excel/Numbers
python3 -m mfaa.cli.main report \
    ./parsed/events.json \
    --format csv \
    --output ./reports/timeline.csv
```

**Use the CSV:**
```bash
# Open in Excel/Numbers
open ./reports/timeline.csv

# Or view in terminal
head -n 20 ./reports/timeline.csv

# Filter high-priority events
awk -F',' '$5 >= 60' ./reports/timeline.csv > high_priority.csv
```

#### 3.3 Generate All Formats

```bash
# Generate HTML, CSV, and JSON in one command
python3 -m mfaa.cli.main report \
    ./parsed/events.json \
    --format all \
    --output ./reports/

# This creates:
# - timeline.html (interactive web report)
# - timeline.csv (spreadsheet)
# - timeline.json (programmatic access)
```

---

### Step 4: Filter Documents Folder Activity

**What it does:** Focus analysis on ~/Documents folder only.

```bash
# Create filtered timeline for Documents folder
python3 -m mfaa.cli.main report \
    ./parsed/events.json \
    --format html \
    --output ./reports/documents_only.html \
    --theme light

# Note: The filtering is done by pattern matching in the timeline
# You can manually filter the JSON before reporting
```

**Manual filtering with jq:**
```bash
# Install jq if not available
# brew install jq

# Filter events in Documents folder
jq '[.events[] | select(.path | contains("/Documents/"))]' \
    ./parsed/events.json > ./parsed/documents_events.json

# Generate report from filtered data
python3 -m mfaa.cli.main report \
    ./parsed/documents_events.json \
    --format html \
    --output ./reports/documents_timeline.html
```

---

## Understanding the Results

### HTML Report Sections

#### 1. Executive Summary

Located at the top of the HTML report:

```
📊 Executive Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Events Analyzed: 45,678
Time Range: Sep 1, 2025 - Oct 26, 2025 (56 days)

Priority Distribution:
  🔴 CRITICAL (80-100):     234 events (0.5%)
  🟠 HIGH (60-79):        1,000 events (2.2%)
  🟡 MEDIUM (40-59):      5,678 events (12.4%)
  🟢 LOW (0-39):         38,766 events (84.9%)

Suspicious Patterns:
  ⚠️  Data Exfiltration: 1 instance detected
     • 234 files moved to external volume
     • Time: Oct 15, 2025 14:32:15

  ⚠️  Suspicious Execution: 2 instances detected
     • Downloaded script executed from ~/Downloads
     • Time: Oct 20, 2025 09:15:43
```

**What this means:**
- Most events (84.9%) are normal file operations
- 2.7% are high-priority events that warrant investigation
- 3 suspicious patterns were detected automatically

#### 2. Interactive Timeline

The main timeline view shows:

**Timeline Features:**
- **Zoom:** Scroll to zoom in/out on specific time periods
- **Pan:** Drag to move through time
- **Filter:** Click priority badges to filter by category
- **Search:** Search for specific files or paths
- **Details:** Click any event to see full details

**Example Event Details:**
```json
{
  "event_id": 12345,
  "timestamp": "2025-10-20T09:15:43",
  "path": "/Users/anhnlq/Downloads/suspicious_script.sh",
  "event_types": ["Created", "IsFile"],
  "priority_score": 87,
  "priority_category": "CRITICAL",
  "xattr": {
    "quarantine": true,
    "download_source": "https://suspicious-site.com/script.sh",
    "downloaded_by": "com.apple.Safari"
  },
  "notes": [
    "Downloaded file with quarantine flag",
    "Script executed within 5 minutes of download",
    "Part of 'Suspicious Execution' pattern"
  ]
}
```

**What this tells you:**
- A script was downloaded from the internet
- It has quarantine flag (macOS security feature)
- It was executed shortly after download (suspicious)
- Downloaded via Safari

#### 3. Pattern Analysis

Shows detected threat patterns:

**Example: Data Exfiltration Pattern**
```
Pattern: Data Exfiltration
Severity: HIGH
Confidence: 85%

Description:
  Large volume of files (234 files, 1.2 GB) were copied to
  external volume "/Volumes/USB_DRIVE" in a short time window.

Timeline:
  Start: Oct 15, 2025 14:32:15
  End:   Oct 15, 2025 14:45:30
  Duration: 13 minutes

Files Involved:
  • /Users/anhnlq/Documents/Projects/ClientData/*.xlsx (45 files)
  • /Users/anhnlq/Documents/Financial/*.pdf (89 files)
  • /Users/anhnlq/Documents/Confidential/*.docx (100 files)

Recommendation:
  ⚠️  Investigate: Verify if this data transfer was authorized
  🔍 Review: Check if external drive is company-approved
  📋 Document: Record findings in incident report
```

#### 4. Statistics Dashboard

**File Type Distribution:**
```
Documents:    15,234 events (33.4%)
Images:        8,765 events (19.2%)
Code Files:    5,432 events (11.9%)
Archives:      2,345 events (5.1%)
Others:       13,902 events (30.4%)
```

**Most Active Directories:**
```
1. /Users/anhnlq/Documents/        12,345 events
2. /Users/anhnlq/Downloads/         8,765 events
3. /Users/anhnlq/Desktop/           5,432 events
4. /Applications/                   3,210 events
5. /Users/anhnlq/Library/           2,345 events
```

**Temporal Distribution:**
```
[Heatmap showing activity by hour and day of week]

Peak Activity:
  • Monday 9-11 AM: 2,345 events
  • Friday 3-5 PM: 1,987 events

Unusual Activity:
  • Saturday 2 AM: 234 events (unusual for weekend early morning)
```

---

## Advanced Analysis

### Scenario 1: Investigating Downloaded Files

**Goal:** Find all files downloaded in the last 7 days.

```bash
# Filter events with quarantine xattr (downloaded files)
jq '[.events[] | select(.xattr.quarantine == true) |
    select(.timestamp > "2025-10-19")]' \
    ./parsed/events.json > downloads_recent.json

# Generate report
python3 -m mfaa.cli.main report \
    downloads_recent.json \
    --format html \
    --output ./reports/recent_downloads.html
```

### Scenario 2: Tracking Specific File

**Goal:** See complete history of a specific document.

```bash
# Track a specific file
FILE_PATH="/Users/anhnlq/Documents/important_document.pdf"

jq "[.events[] | select(.path == \"$FILE_PATH\")]" \
    ./parsed/events.json > file_history.json

# View chronological history
jq -r '.[] | "\(.timestamp) \(.event_types | join(",")) \(.path)"' \
    file_history.json
```

**Example output:**
```
2025-10-15T10:30:00 Created /Users/anhnlq/Documents/important_document.pdf
2025-10-15T10:31:15 Modified /Users/anhnlq/Documents/important_document.pdf
2025-10-15T10:35:42 Modified /Users/anhnlq/Documents/important_document.pdf
2025-10-20T14:22:33 Renamed /Users/anhnlq/Documents/important_document_final.pdf
2025-10-25T09:15:12 Removed /Users/anhnlq/Documents/important_document_final.pdf
```

### Scenario 3: Finding High-Priority Events

**Goal:** Export only critical and high-priority events.

```bash
# Filter high-priority events (score >= 60)
python3 -c "
import json
with open('./parsed/events.json') as f:
    data = json.load(f)
    # Note: Priority scoring happens during report generation
    # This is a placeholder - actual filtering needs scorer
    print('Use --min-priority flag with report command')
"

# Better approach: Use mFAA's built-in filtering
python3 -m mfaa.cli.main report \
    ./parsed/events.json \
    --format csv \
    --output ./reports/high_priority.csv \
    --min-priority 60
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Permission Denied

**Error:**
```
Error: Permission denied accessing /.fseventsd/
```

**Solution:**
```bash
# Use sudo for collection
sudo python3 -m mfaa.cli.main collect --output ./artifacts

# Or change ownership of output directory
sudo chown -R $(whoami) ./artifacts
```

#### Issue 2: No Events in Documents Folder

**Error:**
```
Warning: No events found in /Users/anhnlq/Documents/
```

**Possible Causes:**
1. Documents folder hasn't been accessed recently
2. FSEvents database was recently cleared
3. Documents is on a different volume

**Solution:**
```bash
# Check which volume Documents is on
df ~/Documents

# If on different volume, collect from that volume
sudo python3 -m mfaa.cli.main collect \
    --volume /Volumes/OtherDrive \
    --output ./artifacts
```

#### Issue 3: Parsing Fails

**Error:**
```
Error: Failed to parse FSEvents file: Invalid format
```

**Solution:**
```bash
# Skip invalid files with validation
python3 -m mfaa.cli.main parse \
    ./artifacts/.fseventsd/ \
    --output ./parsed/events.json \
    --validate

# Check parser logs
tail -f ./mfaa.log
```

#### Issue 4: Report Too Large

**Error:**
```
Warning: Timeline contains 500,000+ events. Report may be slow.
```

**Solution:**
```bash
# Filter by date range (manual with jq)
jq '[.events[] | select(.timestamp > "2025-10-01")]' \
    ./parsed/events.json > recent_events.json

# Or filter by priority
python3 -m mfaa.cli.main report \
    ./parsed/events.json \
    --format html \
    --output ./reports/filtered.html \
    --min-priority 40  # Medium and above only
```

---

## Best Practices

### 1. Regular Collection

```bash
# Create daily collection script
cat > ~/bin/mfaa_daily.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
OUTPUT_DIR="$HOME/mfaa_collections/$DATE"

mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

# Collect
sudo python3 -m mfaa.cli.main collect \
    --output ./artifacts

# Parse
python3 -m mfaa.cli.main parse \
    ./artifacts/Macintosh_HD/.fseventsd/ \
    --output ./events.json

# Report
python3 -m mfaa.cli.main report \
    ./events.json \
    --format all \
    --output ./reports/

echo "Daily collection complete: $OUTPUT_DIR"
EOF

chmod +x ~/bin/mfaa_daily.sh

# Run daily via cron
# 0 2 * * * /Users/anhnlq/bin/mfaa_daily.sh
```

### 2. Case Organization

```bash
# Organize by case
mkdir -p ~/forensics_cases/CASE-2025-001
cd ~/forensics_cases/CASE-2025-001

# Document everything
cat > case_notes.txt << EOF
Case ID: CASE-2025-001
Date: $(date)
Investigator: John Doe
Description: Suspicious file activity in Documents folder

Collection Info:
- Source: Macintosh HD (/)
- Collection Time: $(date)
- mFAA Version: 1.0.0
EOF

# Collect evidence
sudo python3 -m mfaa.cli.main collect --output ./evidence
```

### 3. Chain of Custody

```bash
# Verify integrity of collected evidence
cat ./artifacts/Macintosh_HD/acquisition_log.json

# Example output shows SHA-256 hashes
{
  "volume_name": "Macintosh HD",
  "collected_at": "2025-10-26T10:30:00",
  "sha256_hashes": {
    "0000000000abcdef": "a1b2c3d4e5f6...",
    "0000000000fedcba": "f6e5d4c3b2a1..."
  }
}

# Re-verify hashes later
shasum -a 256 ./artifacts/Macintosh_HD/.fseventsd/*
```

---

## Next Steps

After completing this tutorial:

1. **Explore Advanced Features**
   - [Configuration Guide](../configuration/configuration-guide.md) - Customize scoring weights
   - [Command Reference](command-reference.md) - Learn all CLI options
   - [Pattern Detection](../configuration/configuration-guide.md#pattern-detection) - Configure custom patterns

2. **Real-World Scenarios**
   - Incident response workflows
   - Malware analysis techniques
   - Data breach investigations

3. **Automation**
   - Create collection scripts
   - Automate daily snapshots
   - Integrate with SIEM

---

## Summary

You've learned how to:

✅ Collect FSEvents from your macOS system
✅ Parse binary FSEvents into structured JSON
✅ Generate interactive HTML reports
✅ Analyze file system activity in Documents folder
✅ Interpret priority scores and patterns
✅ Troubleshoot common issues

**Key Takeaways:**

1. **Collection requires sudo** - FSEvents database needs root access
2. **Parsing is fast** - Even large databases parse in seconds
3. **Reports are interactive** - HTML reports include zoom, filter, search
4. **Priority scoring is automatic** - No configuration needed for basic use
5. **Patterns are detected automatically** - 5 built-in threat patterns

---

## Additional Resources

- **[Getting Started](getting-started.md)** - Installation and basics
- **[Command Reference](command-reference.md)** - Complete CLI docs
- **[Configuration Guide](../configuration/configuration-guide.md)** - Advanced customization
- **[Troubleshooting](getting-started.md#next-steps)** - Common issues and solutions

---

**Tutorial Version:** 1.0.0
**Last Updated:** 2025-10-26
**Tested On:** macOS 14.0 (Sonoma)

[⬆ Back to top](#practical-tutorial-analyzing-your-documents-folder)
