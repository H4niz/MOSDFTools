# Demo Walkthrough: Running mFAA with Test Data

**Level:** Beginner
**Time:** 10 minutes
**Environment:** Any macOS system

This walkthrough demonstrates mFAA using sample FSEvents data, avoiding the need for root privileges and System Integrity Protection (SIP) issues.

---

## 🚨 Important Note: FSEvents Collection on Modern macOS

### Why Direct Collection May Fail

On modern macOS systems (10.14+), accessing `/.fseventsd` is restricted by **System Integrity Protection (SIP)**, even with `sudo`:

```bash
sudo ls /.fseventsd
# May show: Operation not permitted
```

### Collection Options

| Method | Requirements | Use Case |
|--------|--------------|----------|
| **Direct Collection** | SIP disabled | Forensic workstation, lab environment |
| **Recovery Mode** | Boot to Recovery | Live forensics on target machine |
| **External Mount** | Target as external drive | Dead box forensics |
| **Test Data** | None | Development, testing, training |

---

## Option 1: Using Test Data (Recommended for Demo)

### Step 1: Create Test Environment

```bash
# Navigate to mFAA directory
cd /Users/anhnlq/Documents/GitHub/MOSDFTools

# Activate virtual environment
source .venv/bin/activate

# Create demo directory
mkdir -p demo_data/test_fsevents
cd demo_data
```

### Step 2: Generate Sample FSEvents Data

```bash
# Create a simple test FSEvents file structure
mkdir -p test_volume/.fseventsd
cd test_volume

# Create some test files to generate events
touch Documents/test_file.txt
mkdir Downloads
touch Downloads/sample.pdf
echo "test" > Desktop/note.txt

# Note: These are just placeholders - real FSEvents are binary
# For a real demo, you would need actual FSEvents files
```

### Step 3: Parse Sample Data

Since we can't easily create valid binary FSEvents files, let's use the parser test data:

```bash
cd /Users/anhnlq/Documents/GitHub/MOSDFTools

# Run parser tests to see how parsing works
source .venv/bin/activate
python3 -m pytest tests/test_fsevents_parser.py -v

# This shows the parser in action with test data
```

### Step 4: Generate Sample Timeline

Create a sample events JSON file manually:

```bash
cat > demo_data/sample_events.json << 'EOF'
{
  "events": [
    {
      "event_id": 1,
      "timestamp": "2025-10-26T10:00:00",
      "path": "/Users/demo/Documents/important.pdf",
      "flags": ["ITEM_CREATED", "ITEM_IS_FILE"],
      "node_id": 12345
    },
    {
      "event_id": 2,
      "timestamp": "2025-10-26T10:05:00",
      "path": "/Users/demo/Documents/important.pdf",
      "flags": ["ITEM_MODIFIED", "ITEM_IS_FILE"],
      "node_id": 12345
    },
    {
      "event_id": 3,
      "timestamp": "2025-10-26T10:10:00",
      "path": "/Users/demo/Downloads/suspicious.sh",
      "flags": ["ITEM_CREATED", "ITEM_IS_FILE"],
      "node_id": 12346
    },
    {
      "event_id": 4,
      "timestamp": "2025-10-26T14:30:00",
      "path": "/Users/demo/Documents/important.pdf",
      "flags": ["ITEM_REMOVED", "ITEM_IS_FILE"],
      "node_id": 12345
    }
  ],
  "metadata": {
    "total_events": 4,
    "parsed_at": "2025-10-26T15:00:00",
    "source": "sample_data"
  }
}
EOF
```

### Step 5: Generate Report from Sample Data

```bash
# Generate HTML report
python3 -m mfaa.cli.main report \
    demo_data/sample_events.json \
    --format html \
    --output demo_data/report.html

# Open the report
open demo_data/report.html
```

---

## Option 2: External Drive Forensics (Real Data)

### When to Use

- Analyzing a suspect's drive
- Post-mortem forensics
- Drive is removed from original system

### Prerequisites

- Target macOS drive connected as external
- USB/Thunderbolt adapter
- Read-only mounting recommended

### Steps

```bash
# 1. Connect external drive
# Drive appears at: /Volumes/ExternalMac

# 2. Verify FSEvents directory exists
ls -la /Volumes/ExternalMac/.fseventsd/

# 3. Collect (NO sudo needed for external drives)
python3 -m mfaa.cli.main collect \
    --volume /Volumes/ExternalMac \
    --output ./external_analysis \
    --include-xattr

# 4. Parse
python3 -m mfaa.cli.main parse \
    ./external_analysis/collection_*/fsevents/.fseventsd/ \
    --output ./external_analysis/events.json

# 5. Generate report
python3 -m mfaa.cli.main report \
    ./external_analysis/events.json \
    --format all \
    --output ./external_analysis/reports/
```

---

## Option 3: Recovery Mode Collection (Live System)

### When to Use

- Need FSEvents from running system
- SIP is enabled (default)
- Have physical access

### Steps

#### 1. Boot to Recovery Mode

```
1. Restart Mac
2. Hold ⌘ + R during boot
3. Wait for Recovery Mode to load
4. Open Terminal from Utilities menu
```

#### 2. Disable SIP Temporarily

```bash
# In Recovery Terminal
csrutil disable

# Reboot normally
reboot
```

#### 3. Collect FSEvents

```bash
# Now in normal macOS (SIP disabled)
cd /Users/anhnlq/Documents/GitHub/MOSDFTools
source .venv/bin/activate

# Collection will now work
sudo python3 -m mfaa.cli.main collect \
    --volume / \
    --output ./live_collection \
    --include-xattr \
    --verify-hashes
```

#### 4. Re-enable SIP

```bash
# Boot back to Recovery Mode
# In Recovery Terminal:
csrutil enable
reboot
```

**⚠️ Warning:** Disabling SIP reduces system security. Only do this on forensic workstations or with proper authorization.

---

## Option 4: Using Test Suite Data

### Quick Demo Without Real FSEvents

```bash
cd /Users/anhnlq/Documents/GitHub/MOSDFTools
source .venv/bin/activate

# Run the test suite to see mFAA in action
python3 -m pytest tests/integration/ -v --tb=short

# This runs complete workflows with test data:
# - Collection (mocked)
# - Parsing (real parser, test data)
# - Analysis (real analyzer)
# - Reporting (real reports)

# View generated test reports
ls -la tests/integration/output/
```

---

## Understanding the Commands

### Collection Command Explained

```bash
sudo python3 -m mfaa.cli.main collect \
    --volume /                    # Volume to analyze (/ = root)
    --output ./artifacts          # Where to save collected data
    --include-xattr               # Include extended attributes
    --verify-hashes               # Calculate SHA-256 hashes
```

**Output Structure:**
```
artifacts/
└── collection_20251026_213856/
    ├── fsevents/
    │   └── .fseventsd/          # Copied FSEvents files
    │       ├── 0000000000abcdef
    │       ├── 0000000000fedcba
    │       └── ...
    ├── acquisition_log.json     # Collection metadata
    └── xattr_records.json       # Extended attributes
```

### Parse Command Explained

```bash
python3 -m mfaa.cli.main parse \
    ./artifacts/collection_*/fsevents/.fseventsd/ \  # Input directory
    --output ./events.json                            # Output file
    --format json                                     # Format (json/json-compact)
```

**Output:** Structured JSON with all FSEvents decoded

### Report Command Explained

```bash
python3 -m mfaa.cli.main report \
    ./events.json              # Input timeline JSON
    --format html              # html, csv, json, or all
    --output ./report.html     # Output file
    --theme light              # Theme (light/dark)
```

**Output:** Interactive HTML report with:
- Timeline visualization
- Priority scoring
- Pattern detection
- Statistics dashboard

---

## Troubleshooting Common Issues

### Issue 1: SIP Blocks Access

**Error:**
```
❌ FSEvents collection failed: FSEvents directory not found: /.fseventsd
```

**Solutions:**
1. Use external drive method (Option 2)
2. Disable SIP in Recovery Mode (Option 3)
3. Use test data for demo (Option 1)
4. Check if running on proper macOS version

### Issue 2: Permission Denied Even with Sudo

**Error:**
```
Operation not permitted
```

**Cause:** System Integrity Protection (SIP) is enabled

**Verification:**
```bash
csrutil status
# Output: System Integrity Protection status: enabled
```

**Solutions:**
- See Option 3 (Recovery Mode)
- Or use external drive (Option 2)

### Issue 3: Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'mfaa'
```

**Solution:**
```bash
# Make sure you're in the right directory
cd /Users/anhnlq/Documents/GitHub/MOSDFTools

# Activate virtual environment
source .venv/bin/activate

# Reinstall if needed
pip install -e .
```

---

## Best Practices for Real Forensics

### 1. Read-Only Mounting

```bash
# Mount external drive read-only
diskutil mount readOnly /dev/disk2s1

# Verify read-only
mount | grep disk2s1
# Should show: ... read-only ...
```

### 2. Hash Verification

```bash
# Always use --verify-hashes
python3 -m mfaa.cli.main collect \
    --volume /Volumes/Evidence \
    --output ./case_001 \
    --verify-hashes

# Later verify integrity
cat ./case_001/collection_*/acquisition_log.json
# Check SHA-256 hashes match
```

### 3. Documentation

```bash
# Create case notes
cat > case_notes.txt << EOF
Case ID: CASE-2025-001
Date: $(date)
Analyst: Your Name
Subject: Suspicious activity investigation

Collection Info:
- Source: /Volumes/SuspectDrive
- Collection Time: $(date)
- mFAA Version: 1.0.0
- SIP Status: Enabled (external drive)
- Hash Algorithm: SHA-256

Notes:
- Drive was write-protected during collection
- No modifications made to source data
- All artifacts collected to isolated analysis machine
EOF
```

### 4. Chain of Custody

```bash
# Document every step
mkdir -p case_001/documentation

# Copy acquisition log
cp ./case_001/collection_*/acquisition_log.json \
   ./case_001/documentation/

# Add your notes
cp case_notes.txt ./case_001/documentation/

# Create timeline of actions
cat >> ./case_001/documentation/chain_of_custody.txt << EOF
$(date): Drive connected to analysis workstation
$(date): FSEvents collection initiated
$(date): Collection completed successfully
$(date): Hashes verified
$(date): Analysis began
EOF
```

---

## Example Workflows

### Workflow 1: Quick Triage

```bash
# 1. Connect suspect drive
# 2. Quick collection (no xattr for speed)
python3 -m mfaa.cli.main collect \
    --volume /Volumes/SuspectDrive \
    --output ./triage \
    --no-xattr

# 3. Parse
python3 -m mfaa.cli.main parse \
    ./triage/collection_*/fsevents/.fseventsd/ \
    --output ./triage/events.json

# 4. Generate executive summary
python3 -m mfaa.cli.main report \
    ./triage/events.json \
    --format executive \
    --output ./triage/summary.html \
    --min-priority 60

# 5. Review high-priority events only
open ./triage/summary.html
```

### Workflow 2: Detailed Investigation

```bash
# 1. Full collection with all features
python3 -m mfaa.cli.main collect \
    --volume /Volumes/Evidence \
    --output ./investigation \
    --include-xattr \
    --verify-hashes

# 2. Parse with validation
python3 -m mfaa.cli.main parse \
    ./investigation/collection_*/fsevents/.fseventsd/ \
    --output ./investigation/events.json \
    --validate

# 3. Generate all report formats
python3 -m mfaa.cli.main report \
    ./investigation/events.json \
    --format all \
    --output ./investigation/reports/

# 4. Analyze results
open ./investigation/reports/timeline_report.html
open ./investigation/reports/timeline_report.csv
```

---

## Next Steps

After completing this demo walkthrough:

1. **Practice with Test Data** - Use Option 1 to understand the workflow
2. **Try External Drive** - If you have a spare macOS drive, use Option 2
3. **Explore Reports** - Study the HTML report features
4. **Learn Advanced Features** - Check [Configuration Guide](../configuration/configuration-guide.md)
5. **Read Best Practices** - Review forensic investigation guidelines

---

## Summary

**Key Takeaways:**

✅ **SIP blocks direct FSEvents access** - Normal on modern macOS
✅ **Multiple collection methods** - Choose based on your situation
✅ **Test data works** - Practice without real FSEvents
✅ **External drives** - Best option for real forensics
✅ **Documentation crucial** - Always document your process

**Collection Methods Comparison:**

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Test Data** | No privileges needed | Not real data | Learning, demo |
| **External Drive** | No SIP issues | Need physical drive | Real forensics |
| **Recovery Mode** | Full system access | Risky, requires reboot | Live investigation |
| **SIP Disabled** | Direct access | Security risk | Forensic workstation |

---

## Additional Resources

- **[Practical Tutorial](practical-tutorial.md)** - Detailed walkthrough (assumes SIP disabled)
- **[Command Reference](command-reference.md)** - Complete CLI documentation
- **[Troubleshooting Guide](getting-started.md)** - Common issues
- **[Apple SIP Documentation](https://support.apple.com/en-us/HT204899)** - Official SIP info

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-26
**Tested On:** macOS 14.0 (Sonoma) with SIP enabled

[⬆ Back to top](#demo-walkthrough-running-mfaa-with-test-data)
