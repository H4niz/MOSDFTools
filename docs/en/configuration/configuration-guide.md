# Configuration Guide

Customize mFAA's behavior through configuration files, environment variables, and command-line options.

---

## Table of Contents

1. [Configuration Files](#configuration-files)
2. [Priority Scoring](#priority-scoring)
3. [Pattern Detection](#pattern-detection)
4. [Report Customization](#report-customization)
5. [Advanced Settings](#advanced-settings)

---

## Configuration Files

### Default Configuration Locations

mFAA searches for configuration files in the following order:

1. `./mfaa.yml` (current directory)
2. `~/.mfaa/config.yml` (user home)
3. `/etc/mfaa/config.yml` (system-wide)

### Configuration File Format

```yaml
# mfaa.yml - Main configuration file

# Logging configuration
logging:
  level: INFO          # DEBUG, INFO, WARNING, ERROR
  format: detailed     # simple, detailed, json
  file: ./mfaa.log     # Log file path (optional)

# Collection settings
collection:
  verify_hashes: true  # Calculate SHA-256 for collected files
  include_xattr: true  # Collect extended attributes
  buffer_size: 8192    # Read buffer size (bytes)

# Parser settings
parser:
  validate_events: true  # Filter invalid events
  max_path_length: 1024  # Maximum path length
  skip_system_files: false  # Skip system-generated events

# Analysis settings
analysis:
  detect_patterns: true  # Enable pattern detection
  min_priority: 0        # Minimum priority score (0-100)

# Report settings
report:
  theme: light          # light, dark
  open_browser: false   # Auto-open HTML reports
  include_statistics: true

# Custom weights (see Priority Scoring section)
weights:
  event_types: {...}
  paths: {...}
  file_types: {...}
```

---

## Priority Scoring

### Overview

Priority scoring assigns a **0-100 score** to each event based on:
- Event type (Created, Removed, Modified, etc.)
- Path sensitivity (system paths, user directories)
- File type risk (executables, scripts, documents)
- Extended attributes (quarantine, download source)

### Default Weights

#### Event Type Weights (0-10)

```yaml
weights:
  event_types:
    Removed: 10        # File deletion
    Created: 5         # File creation
    Renamed: 7         # File rename/move
    Modified: 3        # File modification
    InodeMetaMod: 3    # Metadata change
    ChangeOwner: 6     # Ownership change
    XAttrMod: 4        # Extended attribute change
    FinderInfoMod: 2   # Finder info change
```

#### Path Weights (0-10)

```yaml
weights:
  paths:
    '^/System/': 10                          # System files
    '^/Library/LaunchDaemons/': 10           # Launch daemons (persistence)
    '^/Users/.*/Library/LaunchAgents/': 9    # Launch agents (persistence)
    '^/Applications/': 8                     # Applications
    '^/usr/(s)?bin/': 9                      # System binaries
    '^/Users/.*/Downloads/': 7               # Downloads folder
    '^/Users/.*/Desktop/': 6                 # Desktop
    '^/tmp/': 6                              # Temporary files
    '^/var/tmp/': 6                          # Temporary files
```

#### File Type Weights (0-10)

```yaml
weights:
  file_types:
    # Executables
    .app: 10
    .command: 10
    .sh: 9
    .bash: 9
    .zsh: 9
    .py: 7
    .pl: 7
    .rb: 7
    .jar: 8
    .pkg: 8
    .dmg: 7
    .exe: 10
    .dll: 10
    .scr: 10

    # Suspicious extensions
    .encrypted: 10
    .locked: 10
    .crypt: 10

    # Documents
    .pdf: 3
    .doc: 3
    .docx: 3
    .xls: 3
    .xlsx: 3

    # Archives
    .zip: 6
    .tar: 6
    .gz: 6
```

#### Bonus Scores

```yaml
weights:
  quarantine_bonus: 5   # File has quarantine xattr
  download_bonus: 5     # File has download source
```

### Score Calculation

```
Raw Score = Event Weight + Path Weight + File Type Weight + Bonuses
Max Raw Score = 10 + 10 + 10 + 5 + 5 = 40
Normalized Score = (Raw Score / 40) * 100

Priority Categories:
- CRITICAL: 80-100
- HIGH: 60-79
- MEDIUM: 40-59
- LOW: 0-39
```

### Customizing Weights

**Example: Focus on persistence mechanisms**

```yaml
# custom_weights.yml
weights:
  event_types:
    Created: 10      # Increase from 5
    Renamed: 10      # Increase from 7

  paths:
    '^/Library/LaunchDaemons/': 10
    '^/Users/.*/Library/LaunchAgents/': 10
    '^/System/Library/Extensions/': 10  # Add kernel extensions
    '^/Users/.*/Library/Preferences/': 8  # Add preferences

  file_types:
    .plist: 10       # Add property lists
    .kext: 10        # Add kernel extensions
```

**Usage:**

```bash
# Use custom configuration
mfaa analyze --config custom_weights.yml --volume / --output ./analysis
```

---

## Pattern Detection

### Built-in Patterns

mFAA detects 5 threat patterns:

#### 1. Ransomware Encryption

**Indicators:**
- Multiple files renamed with suspicious extensions (`.encrypted`, `.locked`, `.crypt`)
- High volume of file modifications/renames in short time
- Ransom notes created (`.txt`, `.html` with keywords)

**Configuration:**

```yaml
patterns:
  ransomware:
    enabled: true
    suspicious_extensions:
      - .encrypted
      - .locked
      - .crypt
      - .encr
      - .crypted
    min_affected_files: 10  # Minimum files to trigger
    time_window_minutes: 60  # Detection window
    ransom_note_keywords:
      - "ransom"
      - "bitcoin"
      - "decrypt"
      - "payment"
```

#### 2. Data Exfiltration

**Indicators:**
- Large archives created in Downloads/Desktop
- Files moved to external volumes
- Compressed files with sensitive data patterns

**Configuration:**

```yaml
patterns:
  exfiltration:
    enabled: true
    archive_extensions:
      - .zip
      - .tar
      - .gz
      - .7z
      - .rar
    min_archive_size_mb: 100  # Minimum size to flag
    sensitive_paths:
      - /Users/.*/Documents/
      - /Users/.*/Desktop/
      - /Applications/
```

#### 3. Persistence Installation

**Indicators:**
- LaunchAgents/LaunchDaemons creation
- Login Items modification
- Startup scripts created

**Configuration:**

```yaml
patterns:
  persistence:
    enabled: true
    monitored_paths:
      - /Library/LaunchDaemons/
      - /Users/.*/Library/LaunchAgents/
      - /Users/.*/Library/Preferences/loginwindow.plist
      - /etc/rc.common
    suspicious_names:
      - "com.unknown.*"
      - ".*backdoor.*"
      - ".*trojan.*"
```

#### 4. Suspicious Execution

**Indicators:**
- Scripts executed from unusual locations
- Downloaded executables run immediately
- Unsigned applications launched

**Configuration:**

```yaml
patterns:
  suspicious_execution:
    enabled: true
    unusual_execution_paths:
      - /tmp/
      - /var/tmp/
      - /Users/.*/Downloads/
      - /Users/.*/Desktop/
    executable_extensions:
      - .sh
      - .command
      - .app
      - .pkg
    time_after_download_minutes: 5  # Execution within 5 min of download
```

#### 5. Credential Access

**Indicators:**
- Keychain access
- Password files accessed
- Browser profile access

**Configuration:**

```yaml
patterns:
  credential_access:
    enabled: true
    sensitive_files:
      - /Users/.*/Library/Keychains/
      - /Users/.*/Library/Application Support/Google/Chrome/
      - /Users/.*/Library/Application Support/Firefox/
      - /private/var/db/dslocal/nodes/Default/users/
    suspicious_processes:
      - ".*keychain.*"
      - ".*password.*"
      - ".*credential.*"
```

### Custom Pattern Detection

**Example: Monitor specific application**

```yaml
# custom_patterns.yml
patterns:
  custom_app_monitoring:
    enabled: true
    name: "Adobe Photoshop Monitoring"
    description: "Track all Photoshop-related file activity"

    # Define criteria
    criteria:
      paths:
        - /Applications/Adobe Photoshop*/
        - /Users/.*/Library/Preferences/com.adobe.Photoshop.plist
        - /Users/.*/Documents/*.psd

      event_types:
        - Created
        - Modified
        - Removed

      file_extensions:
        - .psd
        - .psb
        - .ai

    # Alert thresholds
    thresholds:
      min_events: 5
      time_window_minutes: 30

    # Severity
    severity: MEDIUM
```

---

## Report Customization

### HTML Report Themes

#### Light Theme (Default)

```yaml
report:
  theme: light
  colors:
    primary: "#007bff"
    critical: "#dc3545"
    high: "#fd7e14"
    medium: "#ffc107"
    low: "#28a745"
```

#### Dark Theme

```yaml
report:
  theme: dark
  colors:
    background: "#1a1a1a"
    text: "#e0e0e0"
    primary: "#3498db"
    critical: "#e74c3c"
    high: "#e67e22"
    medium: "#f39c12"
    low: "#2ecc71"
```

#### Custom Theme

```yaml
report:
  theme: custom
  colors:
    background: "#ffffff"
    text: "#333333"
    primary: "#0066cc"
    critical: "#cc0000"
    high: "#ff6600"
    medium: "#ffcc00"
    low: "#009900"
  fonts:
    family: "Arial, sans-serif"
    size: 14px
  layout:
    max_width: 1400px
    sidebar_width: 300px
```

### Report Content

```yaml
report:
  # Sections to include
  sections:
    executive_summary: true
    timeline: true
    patterns: true
    statistics: true
    raw_events: false  # Hide raw event dump

  # Timeline settings
  timeline:
    max_entries: 1000  # Limit entries (0 = no limit)
    group_by: hour     # hour, day, week, month
    show_context: true # Show related events

  # Statistics
  statistics:
    top_paths: 20      # Show top N active paths
    charts: true       # Include visualizations
    heatmap: true      # Temporal heatmap
```

### CSV Export Options

```yaml
report:
  csv:
    delimiter: ","     # Field delimiter
    quote_char: '"'    # Quote character
    encoding: "utf-8"  # File encoding
    include_headers: true
    columns:           # Custom column order
      - timestamp
      - path
      - event_types
      - priority_score
      - priority_category
      - notes
```

---

## Advanced Settings

### Performance Tuning

```yaml
performance:
  # Parser settings
  parser_threads: 4          # Parallel parsing threads
  chunk_size: 1000           # Events per chunk
  memory_limit_mb: 1024      # Memory limit

  # Analysis settings
  batch_size: 500            # Events per batch
  enable_caching: true       # Cache parsed events

  # Report generation
  html_lazy_load: true       # Lazy load timeline entries
  compression: true          # Compress JSON output
```

### Forensics Mode

```yaml
forensics:
  # Strict chain of custody
  verify_integrity: true     # Always verify hashes
  log_all_operations: true   # Detailed audit log
  timestamp_all: true        # Timestamp all operations

  # Evidence preservation
  read_only: true            # Never modify source
  create_backups: true       # Backup before processing

  # Documentation
  case_id: "CASE-2024-001"   # Case identifier
  investigator: "John Doe"   # Investigator name
  notes_file: "./case_notes.txt"  # Case notes
```

### Integration Settings

```yaml
integration:
  # Splunk integration
  splunk:
    enabled: false
    url: "https://splunk.local:8089"
    token: "your-token"
    index: "mfaa"

  # SIEM integration
  siem:
    enabled: false
    format: "cef"      # cef, leef, json
    destination: "syslog://siem.local:514"

  # Webhook notifications
  webhook:
    enabled: false
    url: "https://webhook.site/your-webhook"
    on_events:
      - pattern_detected
      - analysis_complete
      - error
```

---

## Configuration Examples

### Incident Response Configuration

```yaml
# ir_config.yml - Quick triage configuration

logging:
  level: WARNING  # Reduce noise

collection:
  verify_hashes: false  # Skip for speed
  include_xattr: true

analysis:
  min_priority: 60  # High priority only
  detect_patterns: true

report:
  theme: dark
  open_browser: true
  sections:
    executive_summary: true
    patterns: true
    timeline: false  # Skip full timeline
    statistics: true

weights:
  # Focus on execution and persistence
  event_types:
    Created: 10
    Removed: 10
  paths:
    '^/Library/LaunchDaemons/': 10
    '^/tmp/': 10
```

### Malware Analysis Configuration

```yaml
# malware_config.yml - Detailed malware analysis

logging:
  level: DEBUG  # Maximum detail
  file: ./malware_analysis.log

collection:
  verify_hashes: true
  include_xattr: true

analysis:
  min_priority: 0  # Include everything
  detect_patterns: true

patterns:
  # Enable all patterns
  ransomware:
    enabled: true
    min_affected_files: 5
  persistence:
    enabled: true
  suspicious_execution:
    enabled: true
    time_after_download_minutes: 60

report:
  theme: light
  sections:
    executive_summary: true
    timeline: true
    patterns: true
    statistics: true
    raw_events: true  # Include raw data
```

---

## See Also

- [Getting Started](../user-guide/getting-started.md)
- [Command Reference](../user-guide/command-reference.md)
- [Advanced Usage](../user-guide/advanced-usage.md)

---

**Version:** 1.0.0
**Last Updated:** 2025-10-26
