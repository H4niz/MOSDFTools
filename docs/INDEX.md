# Documentation Index

Complete index of all mFAA documentation files.

---

## 📋 Table of Contents

- [Root Documentation](#root-documentation)
- [English Documentation](#english-documentation)
  - [User Guides](#user-guides)
  - [Configuration](#configuration)
  - [Specification](#specification)
  - [Development](#development)
  - [Assessment](#assessment)
- [Vietnamese Documentation](#vietnamese-documentation)

---

## Root Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [README.md](../README.md) | Main project README (bilingual) | ✅ Complete |
| [docs/README.md](README.md) | Documentation overview | ✅ Complete |
| [LICENSE](../LICENSE) | MIT License | ✅ Complete |
| [CLAUDE.md](../CLAUDE.md) | Claude Code configuration | ✅ Complete |

---

## English Documentation

### User Guides

| Document | Description | Status |
|----------|-------------|--------|
| [Getting Started](en/user-guide/getting-started.md) | Installation, quick start, basic workflow | ✅ Complete |
| [Command Reference](en/user-guide/command-reference.md) | Complete CLI documentation | ✅ Complete |
| Advanced Usage | Tips, scripting, advanced features | 🚧 Planned |
| Troubleshooting | Common issues and solutions | 🚧 Planned |

**Topics covered in User Guides:**
- System requirements and installation
- Basic commands: `analyze`, `collect`, `parse`, `report`
- Common use cases (incident response, malware analysis, etc.)
- Output formats (CSV, JSON, HTML)
- Docker usage

---

### Configuration

| Document | Description | Status |
|----------|-------------|--------|
| [Configuration Guide](en/configuration/configuration-guide.md) | Complete configuration reference | ✅ Complete |
| Examples | Configuration examples library | 🚧 Planned |

**Topics covered in Configuration:**
- Configuration file format (YAML)
- Priority scoring weights
- Pattern detection rules
- Report customization
- Performance tuning
- Forensics mode settings
- Integration settings (Splunk, SIEM, webhooks)

---

### Specification

| Document | Description | Status |
|----------|-------------|--------|
| [Business Requirements](en/specification/business-requirements.md) | Full BRD (78KB) | ✅ Complete |
| [Project Summary](en/specification/project-summary.md) | Architecture and implementation | ✅ Complete |
| API Reference | Programmatic API documentation | 🚧 Planned |

**Topics covered in Specification:**
- Requirements and scope
- System architecture
- Module design
- Data models (FSEvent, Timeline, etc.)
- FSEvents v1 and v2/DLS format specs
- Extended attributes parsing
- Priority scoring algorithm
- Pattern detection logic

---

### Development

| Document | Description | Status |
|----------|-------------|--------|
| [Improvement Roadmap](en/development/improvement-roadmap.md) | Future enhancements | ✅ Complete |
| [Changelog](en/development/changelog.md) | Version history | ✅ Complete |
| Contributing Guide | How to contribute | 🚧 Planned |
| Developer Setup | Development environment setup | 🚧 Planned |

**Topics covered in Development:**
- High/medium/low priority improvements
- Feature roadmap (v1.1, v2.0+)
- Resource requirements
- Timeline estimates
- Version history and release notes

---

### Assessment

| Document | Description | Status |
|----------|-------------|--------|
| [Maturity Assessment](en/assessment/maturity-assessment.md) | Quality metrics (90/100) | ✅ Complete |
| [Test Fixes Summary](en/assessment/test-fixes-summary.md) | Recent test improvements | ✅ Complete |
| Performance Benchmarks | Speed and resource usage | 🚧 Planned |

**Topics covered in Assessment:**
- Overall maturity score (90/100)
- Test results (93% pass rate)
- Code coverage (57%)
- BRD requirements compliance
- Gap analysis
- Risk assessment
- Test improvement history

---

## Vietnamese Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [README.md](../README.md#tiếng-việt) | Main README (Vietnamese section) | ✅ Complete |
| User Guide (vi) | Vietnamese user guide | 🚧 Planned |
| Configuration (vi) | Vietnamese configuration guide | 🚧 Planned |

---

## 📊 Documentation Statistics

| Category | Files | Status | Progress |
|----------|-------|--------|----------|
| **Root** | 4 | Complete | 100% |
| **User Guides** | 2/4 | Partial | 50% |
| **Configuration** | 1/2 | Partial | 50% |
| **Specification** | 2/3 | Partial | 67% |
| **Development** | 2/4 | Partial | 50% |
| **Assessment** | 2/3 | Partial | 67% |
| **Vietnamese** | 1/10 | Minimal | 10% |
| **TOTAL** | 14/30 | In Progress | 47% |

---

## 🎯 Documentation Priorities

### Phase 1: Essential (v1.0) ✅ **COMPLETE**
- ✅ README (bilingual)
- ✅ Getting Started
- ✅ Command Reference
- ✅ Configuration Guide
- ✅ Business Requirements
- ✅ Project Summary
- ✅ Maturity Assessment
- ✅ Test Fixes Summary

### Phase 2: Important (v1.1) 🚧 **PLANNED**
- 🚧 Troubleshooting Guide
- 🚧 Advanced Usage
- 🚧 API Reference
- 🚧 Contributing Guide
- 🚧 Developer Setup
- 🚧 Configuration Examples

### Phase 3: Nice-to-Have (v2.0+) 📋 **FUTURE**
- 📋 Performance Benchmarks
- 📋 Complete Vietnamese translation
- 📋 Video tutorials
- 📋 Case studies
- 📋 Integration guides

---

## 📝 Document Metadata

### File Sizes

```
Business Requirements (BRD.md):        78.7 KB
Project Summary:                       21.3 KB
Maturity Assessment:                   20.2 KB
Improvement Roadmap:                   15.4 KB
Test Fixes Summary:                    12.8 KB
Getting Started:                       ~8 KB
Command Reference:                     ~10 KB
Configuration Guide:                   ~12 KB
```

### Last Updated

| Document | Last Updated | Version |
|----------|--------------|---------|
| README.md | 2025-10-26 | 1.0.0 |
| Getting Started | 2025-10-26 | 1.0.0 |
| Command Reference | 2025-10-26 | 1.0.0 |
| Configuration Guide | 2025-10-26 | 1.0.0 |
| Maturity Assessment | 2025-10-26 | 1.0.0 |
| Test Fixes Summary | 2025-10-26 | 1.0.0 |
| Improvement Roadmap | 2025-10-26 | 1.0.0 |

---

## 🔍 Quick Find

### By Task

**Want to install mFAA?**
→ [Getting Started → Installation](en/user-guide/getting-started.md#installation)

**Need command syntax?**
→ [Command Reference](en/user-guide/command-reference.md)

**Want to customize scoring?**
→ [Configuration Guide → Priority Scoring](en/configuration/configuration-guide.md#priority-scoring)

**Looking for architecture details?**
→ [Project Summary → Architecture](en/specification/project-summary.md#architecture)

**Checking project quality?**
→ [Maturity Assessment](en/assessment/maturity-assessment.md)

### By Role

**End Users:**
- [Getting Started](en/user-guide/getting-started.md)
- [Command Reference](en/user-guide/command-reference.md)
- [Configuration Guide](en/configuration/configuration-guide.md)

**Forensics Analysts:**
- [Getting Started → Use Cases](en/user-guide/getting-started.md#common-use-cases)
- [Configuration Guide → Pattern Detection](en/configuration/configuration-guide.md#pattern-detection)
- [Business Requirements → Features](en/specification/business-requirements.md)

**Developers:**
- [Project Summary](en/specification/project-summary.md)
- [Business Requirements](en/specification/business-requirements.md)
- [Improvement Roadmap](en/development/improvement-roadmap.md)

**Managers/Stakeholders:**
- [README.md](../README.md)
- [Maturity Assessment](en/assessment/maturity-assessment.md)
- [Project Summary → Executive Summary](en/specification/project-summary.md#executive-summary)

---

## 📧 Document Requests

Missing documentation? Request it:

1. **Check** this index for planned documents
2. **Search** existing docs - it might be covered elsewhere
3. **Open** an issue if still needed: [GitHub Issues](https://github.com/yourusername/mfaa/issues)

---

**Index Version**: 1.0.0
**Last Updated**: 2025-10-26

[⬆ Back to top](#documentation-index)
