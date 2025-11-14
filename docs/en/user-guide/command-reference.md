# Command Reference

Complete reference for all mFAA CLI commands.

---

## Table of Contents

- [Global Options](#global-options)
- [Commands](#commands)
  - [analyze](#mfaa-analyze)
  - [collect](#mfaa-collect)
  - [parse](#mfaa-parse)
  - [report](#mfaa-report)
- [Exit Codes](#exit-codes)
- [Environment Variables](#environment-variables)

---

## Global Options

Available for all commands:

```bash
mfaa [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `-v, --verbose` | Enable verbose logging |
| `--debug` | Enable debug logging |
| `--help` | Show help message |

**Examples:**

```bash
# Show version
mfaa --version

# Run with verbose output
mfaa --verbose analyze --volume / --output ./analysis

# Enable debug mode
mfaa --debug collect --volume / --output ./evidence
```

---

## Commands

### mfaa analyze

**Full forensic analysis pipeline** - Collects, parses, analyzes, and generates reports.

```bash
mfaa analyze [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--volume` | PATH | `/` | Volume to analyze |
| `-o, --output` | PATH | **Required** | Output directory for analysis results |
| `-f, --format` | CHOICE | `html` | Report format: `csv`, `json`, `html`, `executive`, `all` |
| `--skip-collection` | FLAG | `False` | Skip collection phase (use existing data) |
| `--open-browser` | FLAG | `False` | Open HTML report in browser |
| `--min-priority` | INT | `0` | Minimum priority score (0-100) |

#### Examples

```bash
# Full analysis with HTML report
sudo mfaa analyze --volume / --output ./analysis

# Generate all report formats
sudo mfaa analyze --volume / --output ./analysis --format all

# Skip collection (use existing evidence)
mfaa analyze --output ./analysis --skip-collection

# High-priority events only
sudo mfaa analyze --volume / --output ./analysis --min-priority 60

# Open report automatically
sudo mfaa analyze --volume / --output ./analysis --open-browser
```

#### Output Structure

```
analysis/
├── evidence/
│   └── Macintosh_HD/
│       ├── .fseventsd/
│       ├── acquisition_log.json
│       └── xattr_records.json
├── timeline.json
├── timeline_report.html
├── timeline_report.csv
└── timeline_report.json
```

---

### mfaa collect

**Collect FSEvents and extended attributes** from a volume.

```bash
mfaa collect [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--volume` | PATH | `/` | Volume to collect from |
| `-o, --output` | PATH | **Required** | Output directory |
| `--include-xattr / --no-xattr` | FLAG | `True` | Collect extended attributes |
| `--verify-hashes` | FLAG | `False` | Calculate SHA-256 for collected files |

#### Examples

```bash
# Collect from root volume
sudo mfaa collect --volume / --output ./evidence

# Collect from external drive
sudo mfaa collect --volume /Volumes/External --output ./external_evidence

# Skip extended attributes (faster)
sudo mfaa collect --volume / --output ./evidence --no-xattr

# Collect with hash verification
sudo mfaa collect --volume / --output ./evidence --verify-hashes
```

#### Output Structure

```
evidence/
└── Macintosh_HD/
    ├── .fseventsd/
    │   ├── 0000000000abcdef
    │   ├── 0000000000fedcba
    │   └── ...
    ├── acquisition_log.json
    └── xattr_records.json (if --include-xattr)
```

#### Acquisition Log Format

```json
{
  "volume_name": "Macintosh HD",
  "collected_at": "2024-01-15T10:00:00",
  "collector_version": "1.0.0",
  "files_collected": 42,
  "total_size_bytes": 1048576,
  "sha256_hashes": {
    "0000000000abcdef": "abc123..."
  }
}
```

---

### mfaa parse

**Parse FSEvents files** into structured JSON format.

```bash
mfaa parse INPUT_PATH [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `INPUT_PATH` | FSEvents file or directory to parse |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-o, --output` | PATH | **Required** | Output JSON file |
| `--format` | CHOICE | `json` | Format: `json` (pretty), `json-compact` |
| `--validate` | FLAG | `False` | Validate events (filter invalid) |

#### Examples

```bash
# Parse single FSEvents file
mfaa parse ./evidence/.fseventsd/0000000000abcdef --output events.json

# Parse entire directory
mfaa parse ./evidence/.fseventsd/ --output all_events.json

# Use compact format (smaller file)
mfaa parse ./evidence/.fseventsd/ --output events.json --format json-compact

# Parse with validation
mfaa parse ./evidence/.fseventsd/ --output events.json --validate
```

#### Output Format

**Standard JSON:**
```json
{
  "events": [
    {
      "event_id": 1,
      "timestamp": "2024-01-15T10:00:00",
      "path": "/Users/test/document.txt",
      "flags": ["ITEM_CREATED", "ITEM_IS_FILE"],
      "node_id": 12345
    }
  ],
  "metadata": {
    "total_events": 1,
    "parsed_at": "2024-01-15T10:05:00"
  }
}
```

**Compact JSON:**
```json
{"events":[{"event_id":1,"timestamp":"2024-01-15T10:00:00",...}]}
```

---

### mfaa report

**Generate reports** from parsed timeline JSON.

```bash
mfaa report TIMELINE_FILE [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `TIMELINE_FILE` | Timeline JSON file from parse command |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-f, --format` | CHOICE | `html` | Format: `csv`, `json`, `html`, `executive`, `all` |
| `-o, --output` | PATH | `.` | Output directory |
| `--theme` | CHOICE | `light` | HTML theme: `light`, `dark` |
| `--open-browser` | FLAG | `False` | Open HTML in browser |
| `--min-priority` | INT | `0` | Filter by priority (0-100) |

#### Examples

```bash
# Generate HTML report
mfaa report timeline.json --format html --output ./reports

# Generate all formats
mfaa report timeline.json --format all --output ./reports

# Dark theme HTML
mfaa report timeline.json --format html --theme dark --output ./reports

# High-priority events only (CSV)
mfaa report timeline.json --format csv --min-priority 60 --output ./reports

# Executive summary with auto-open
mfaa report timeline.json --format executive --open-browser
```

#### Report Formats

**CSV:** Spreadsheet-compatible, filterable
```csv
timestamp,event_id,path,event_types,priority_score,priority_category
2024-01-15T10:00:00,1,/Users/test/doc.txt,Created|IsFile,75,HIGH
```

**JSON:** Programmatic access, full details
```json
{
  "timeline": {
    "entries": [...],
    "patterns": [...],
    "statistics": {...}
  }
}
```

**HTML:** Interactive timeline with filters, search, visualizations

**Executive:** High-level summary for management/stakeholders

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid arguments |
| `3` | Permission denied (need root) |
| `4` | File not found |
| `5` | Parse error |

**Examples:**

```bash
# Check exit code
mfaa analyze --volume / --output ./analysis
echo $?  # 0 if successful

# Script error handling
if ! sudo mfaa collect --volume / --output ./evidence; then
    echo "Collection failed with code $?"
    exit 1
fi
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MFAA_LOG_LEVEL` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `MFAA_OUTPUT_DIR` | Default output directory | `.` |
| `MFAA_NO_COLOR` | Disable colored output | `False` |

**Examples:**

```bash
# Enable debug logging
export MFAA_LOG_LEVEL=DEBUG
mfaa analyze --volume / --output ./analysis

# Disable colors
export MFAA_NO_COLOR=1
mfaa collect --volume / --output ./evidence

# Set default output directory
export MFAA_OUTPUT_DIR=/tmp/mfaa_analysis
mfaa analyze --volume /  # outputs to /tmp/mfaa_analysis
```

---

## Advanced Usage

### Chaining Commands

```bash
# Manual pipeline
sudo mfaa collect --volume / --output ./evidence
mfaa parse ./evidence/Macintosh_HD/.fseventsd/ --output events.json
mfaa report events.json --format html --output ./reports
```

### Filtering and Processing

```bash
# High-priority events only
mfaa report timeline.json --min-priority 80 --format csv

# Generate multiple themed reports
mfaa report timeline.json --format html --theme light --output ./light
mfaa report timeline.json --format html --theme dark --output ./dark
```

### Scripting

```bash
#!/bin/bash
# Automated daily collection

DATE=$(date +%Y%m%d)
OUTPUT_DIR="./daily_snapshots/$DATE"

# Collect
if ! sudo mfaa collect --volume / --output "$OUTPUT_DIR"; then
    echo "Collection failed"
    exit 1
fi

# Parse
if ! mfaa parse "$OUTPUT_DIR"/Macintosh_HD/.fseventsd/ --output "$OUTPUT_DIR/events.json"; then
    echo "Parsing failed"
    exit 1
fi

# Report
mfaa report "$OUTPUT_DIR/events.json" --format all --output "$OUTPUT_DIR/reports"

echo "Daily snapshot completed: $OUTPUT_DIR"
```

---

## See Also

- [Getting Started](getting-started.md)
- [Configuration Guide](../configuration/configuration-guide.md)
- [Advanced Usage](advanced-usage.md)
- [Troubleshooting](troubleshooting.md)

---

**Version:** 1.0.0
**Last Updated:** 2025-10-26
