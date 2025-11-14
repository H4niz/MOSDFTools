# mFAA Documentation

Welcome to the mFAA (macOS Forensics Artifacts Analyzer) documentation.

---

## 📚 Documentation Structure

```
docs/
├── en/                    # English documentation
│   ├── user-guide/       # User guides and tutorials
│   ├── configuration/    # Configuration guides
│   ├── specification/    # Technical specifications
│   ├── development/      # Development documentation
│   └── assessment/       # Quality assessments
└── vi/                    # Vietnamese documentation (TBD)
    └── (mirrors en/ structure)
```

---

## 🚀 Quick Links

### For Users

- **[Getting Started](en/user-guide/getting-started.md)** - Installation, basic usage, and quick start
- **[Demo Walkthrough](en/user-guide/demo-walkthrough.md)** - 🆕 SIP issues & test data (START HERE)
- **[Practical Tutorial](en/user-guide/practical-tutorial.md)** - Step-by-step real-world examples
- **[Command Reference](en/user-guide/command-reference.md)** - Complete CLI command documentation
- **[Configuration Guide](en/configuration/configuration-guide.md)** - Customize behavior, weights, and patterns

### For Developers

- **[Project Summary](en/specification/project-summary.md)** - Architecture, design, and implementation
- **[Business Requirements](en/specification/business-requirements.md)** - Full BRD specification
- **[Improvement Roadmap](en/development/improvement-roadmap.md)** - Planned enhancements

### Quality & Assessment

- **[Maturity Assessment](en/assessment/maturity-assessment.md)** - Quality metrics (90/100)
- **[Test Fixes Summary](en/assessment/test-fixes-summary.md)** - Recent test improvements
- **[Changelog](en/development/changelog.md)** - Version history

---

## 📖 Documentation by Topic

### Installation & Setup
- [Getting Started](en/user-guide/getting-started.md#installation) - Installation methods (pip, source, Docker)
- [System Requirements](en/user-guide/getting-started.md#system-requirements) - Prerequisites and dependencies

### Basic Usage
- [Quick Start](en/user-guide/getting-started.md#quick-start) - First analysis in 5 minutes
- [Basic Workflow](en/user-guide/getting-started.md#basic-workflow) - Collection → Parsing → Analysis → Reporting
- [Understanding Output](en/user-guide/getting-started.md#understanding-the-output) - Report formats explained

### Command-Line Interface
- [Global Options](en/user-guide/command-reference.md#global-options) - Common flags for all commands
- [analyze](en/user-guide/command-reference.md#mfaa-analyze) - Full analysis pipeline
- [collect](en/user-guide/command-reference.md#mfaa-collect) - Artifact collection
- [parse](en/user-guide/command-reference.md#mfaa-parse) - FSEvents parsing
- [report](en/user-guide/command-reference.md#mfaa-report) - Report generation

### Configuration
- [Configuration Files](en/configuration/configuration-guide.md#configuration-files) - YAML configuration format
- [Priority Scoring](en/configuration/configuration-guide.md#priority-scoring) - Customize event weights
- [Pattern Detection](en/configuration/configuration-guide.md#pattern-detection) - Threat pattern configuration
- [Report Customization](en/configuration/configuration-guide.md#report-customization) - Themes and formats

### Technical Reference
- [Architecture](en/specification/project-summary.md#architecture) - System design and modules
- [Data Models](en/specification/project-summary.md#data-models) - Event structures and formats
- [FSEvents Formats](en/specification/business-requirements.md#fsevents-analysis) - v1 and v2/DLS parsing

### Development
- [Test Suite](en/assessment/test-fixes-summary.md) - Testing approach and coverage
- [Contributing](../README.md#contributing) - How to contribute
- [Roadmap](en/development/improvement-roadmap.md) - Future development plans

---

## 🌍 Language Versions

| Language | Status | Notes |
|----------|--------|-------|
| **English** | ✅ Complete | Full documentation available |
| **Tiếng Việt** | 🚧 Partial | README translated, other docs planned |

---

## 📝 Documentation Standards

### For Contributors

When contributing documentation:

1. **Format**: Use Markdown (.md) with GitHub-flavored syntax
2. **Structure**: Follow existing document structure
3. **Code Examples**: Include working, tested examples
4. **Screenshots**: Use PNG format, max 1200px width
5. **Links**: Use relative links for internal navigation
6. **Language**:
   - English: Clear, concise, technical
   - Vietnamese: Natural, equivalent translation

### Document Templates

- **User Guide**: [getting-started.md](en/user-guide/getting-started.md)
- **Reference**: [command-reference.md](en/user-guide/command-reference.md)
- **Configuration**: [configuration-guide.md](en/configuration/configuration-guide.md)

---

## 🔍 Search Tips

### Finding Information

**Installation issues?**
- See [Getting Started → Installation](en/user-guide/getting-started.md#installation)

**Command syntax?**
- See [Command Reference](en/user-guide/command-reference.md)

**Customization?**
- See [Configuration Guide](en/configuration/configuration-guide.md)

**Error messages?**
- See [Troubleshooting](en/user-guide/getting-started.md#next-steps) (coming soon)

**API/Library usage?**
- See [Project Summary → Architecture](en/specification/project-summary.md#architecture)

---

## 📧 Feedback

Found an issue with documentation?

- **Typos/Errors**: [Open an issue](https://github.com/yourusername/mfaa/issues)
- **Suggestions**: [Start a discussion](https://github.com/yourusername/mfaa/discussions)
- **Questions**: Check existing documentation first, then ask in Discussions

---

## 📚 Additional Resources

### External Resources
- **Apple FSEvents**: [Apple Developer Documentation](https://developer.apple.com/library/archive/documentation/Darwin/Reference/ManPages/man8/fseventsd.8.html)
- **NIST Guidelines**: [SP 800-86 - Guide to Integrating Forensic Techniques](https://csrc.nist.gov/publications/detail/sp/800-86/final)
- **macOS Forensics**: Community resources and research papers

### Community
- **GitHub Discussions**: Share use cases and techniques
- **Issues**: Report bugs and request features

---

**Version**: 1.0.0
**Last Updated**: 2025-10-26
**Maintained by**: mFAA Development Team

[⬆ Back to top](#mfaa-documentation)
