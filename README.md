# mFAA - macOS Forensics Artifacts Analyzer

<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/mfaa)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-170%2F183%20passing-brightgreen.svg)](docs/en/assessment/test-fixes-summary.md)
[![Coverage](https://img.shields.io/badge/coverage-57%25-yellow.svg)](htmlcov/index.html)
[![Maturity](https://img.shields.io/badge/maturity-90%2F100-success.svg)](docs/en/assessment/maturity-assessment.md)

**A comprehensive digital forensics tool for macOS live acquisition and analysis**

[English](#english) • [Tiếng Việt](#tiếng-việt)

</div>

---

## English

### 🔍 Overview

**mFAA (macOS Forensics Artifacts Analyzer)** is a production-ready digital forensics tool designed for forensics investigators working with modern macOS systems (10.13+) where traditional physical acquisition is challenging due to FileVault 2 encryption on Apple Silicon and T2 Security Chip devices.

### ✨ Key Features

- **🗂️ FSEvents Analysis**: Parse and analyze file system events (v1, v2/DLS, and **v3 formats** - supports macOS Sequoia 15.x)
- **📋 Extended Attributes**: Extract and decode quarantine flags, download sources, and custom metadata
- **⚡ Priority Scoring**: Automatic prioritization of suspicious events with customizable weights
- **🔍 Pattern Detection**: Identify 5 threat patterns:
  - Ransomware encryption activity
  - Data exfiltration attempts
  - Persistence mechanism installation
  - Suspicious script execution
  - Credential access attempts
- **📊 Timeline Generation**: Create chronological timelines with related event grouping
- **📈 Interactive Reports**: Multiple formats (CSV, JSON, HTML) with visualizations
- **🔐 Forensically Sound**: SHA-256 verification, chain of custody logging, read-only operations
- **🔄 Auto-Detection**: Automatically detects and parses FSEvents v1/v2/v3 formats without configuration

### 🎯 Use Cases

- **Incident Response**: Quick triage of system activity
- **Malware Analysis**: Track malicious file operations
- **Data Breach Investigation**: Identify exfiltration patterns
- **User Activity Reconstruction**: Timeline user actions
- **Compliance Auditing**: Document file system changes

### 📦 Requirements

- **OS**: macOS 10.13 (High Sierra) or later (including macOS Sequoia 15.x)
- **Python**: 3.9+
- **Privileges**: Root/Administrator (for FSEvents collection only)
- **File System**: APFS (default on modern macOS)
- **Dependencies**: Listed in `requirements.txt` (auto-installed)

### 🚀 Quick Start

#### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/mfaa.git
cd mfaa

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install mFAA
pip install -e .

# Verify installation
mfaa --version
```

#### Basic Usage

```bash
# Method 1: Full analysis with sudo (collection + analysis)
sudo python3 -m mfaa.cli analyze --volume / --output ./analysis --format html

# Method 2: Quick analysis (using pre-collected data - no sudo needed)
python3 scripts/generate_forensic_report.py

# Open the interactive HTML report
open ./output/forensic_reports/forensic_analysis.html
open ./output/forensic_reports/executive_summary.html
```

#### Advanced Usage

```bash
# Gather available artifacts (scan without collection - no sudo needed)
python3 -m mfaa.cli gather --volume / --output artifact_scan.json

# Collect FSEvents only (requires sudo)
sudo python3 -m mfaa.cli collect --volume / --output-dir ./collected

# Parse collected data (no sudo needed)
python3 -m mfaa.cli parse_cmd ./collected/.fseventsd --output parsed.json

# Generate reports from parsed data
python3 -m mfaa.cli report_cmd parsed.json --format html --output ./reports

# Filter high-priority events only
python3 -m mfaa.cli analyze --output ./analysis --min-priority 70 --format all
```

#### Docker Usage

```bash
# Build Docker image
docker-compose build

# Run analysis in container
docker-compose run --rm mfaa analyze --volume /host --output /output
```

### 📖 Documentation

#### User Documentation
- **[Getting Started](docs/en/user-guide/getting-started.md)** - Installation and basic usage
- **[Command Reference](docs/en/user-guide/command-reference.md)** - Complete CLI documentation
- **[Configuration Guide](docs/en/configuration/configuration-guide.md)** - Customize behavior and weights

#### Technical Documentation
- **[Business Requirements](docs/en/specification/business-requirements.md)** - Full BRD specification
- **[Project Summary](docs/en/specification/project-summary.md)** - Architecture and design
- **[Maturity Assessment](docs/en/assessment/maturity-assessment.md)** - Quality metrics (90/100)

#### Development
- **[Improvement Roadmap](docs/en/development/improvement-roadmap.md)** - Future enhancements
- **[Test Fixes Summary](docs/en/assessment/test-fixes-summary.md)** - Recent improvements
- **[Changelog](docs/en/development/changelog.md)** - Version history

### 🆕 FSEvents v3 Support (macOS Sequoia 15.x)

**New in November 2025:** Full support for macOS Sequoia's FSEvents v3 format!

#### What's New
- ✅ **Auto-detection** of FSEvents v1/v2/v3 formats
- ✅ **Binary format parsing** for `3SLD` header
- ✅ **4.8+ million events** successfully parsed from test system
- ✅ **Zero configuration** - works automatically

#### Tested On
- **macOS Sequoia 15.6.1** (Apple Silicon)
- **2,115 FSEvents files** analyzed
- **100% parsing success rate**

#### Example Results
```bash
$ python3 scripts/generate_forensic_report.py
✓ Parsed 100,000 events from 37 files
✓ Timeline generated with 100,000 entries
✓ Reports: HTML (132 MB), JSON (39 MB), CSV (14 MB)
```

See [`FORENSIC_INVESTIGATION_REPORT.md`](FORENSIC_INVESTIGATION_REPORT.md) for detailed analysis results.

### 🏗️ Architecture

```
mfaa/
├── collector/          # FSEvents and xattr collection
│   ├── fsevents_collector.py
│   ├── xattr_collector.py
│   └── volume_scanner.py
├── parser/             # FSEvents parsing (v1, v2/DLS, v3)
│   ├── fsevents_parser.py  # Auto-detects v1/v2/v3
│   ├── gzip_handler.py
│   └── structures.py
├── analyzer/           # Priority scoring and pattern detection
│   ├── priority_scorer.py
│   └── pattern_detector.py
├── timeline/           # Timeline generation and grouping
│   ├── generator.py
│   └── grouper.py
├── reporter/           # Multi-format report generation
│   ├── csv_reporter.py
│   ├── json_reporter.py
│   └── html_reporter.py
├── cli/                # Command-line interface
│   ├── main.py
│   ├── collect.py
│   ├── parse_cmd.py
│   ├── analyze.py
│   └── report_cmd.py
└── models.py           # Data structures
```

### 📊 Project Status

| Metric | Status | Notes |
|--------|--------|-------|
| **Maturity Score** | 90/100 | Production ready |
| **Test Pass Rate** | 93.0% (170/183) | Improved from 75% |
| **Code Coverage** | 57% | Target: 80% |
| **Modules Complete** | 6/6 (100%) | All features implemented |
| **Documentation** | Comprehensive | English + Vietnamese |

### 🔬 Testing

```bash
# Run all tests
source .venv/bin/activate
pytest tests/ -v --cov=mfaa --cov-report=html

# Run specific test suite
pytest tests/test_timeline_generator.py -v

# View coverage report
open htmlcov/index.html
```

### 🤝 Contributing

Contributions are welcome! Please see our contributing guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

- FSEvents format documentation from Apple Developer resources
- Digital forensics community for testing and feedback

### 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/mfaa/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mfaa/discussions)

---

## Tiếng Việt

### 🔍 Tổng quan

**mFAA (macOS Forensics Artifacts Analyzer)** là công cụ điều tra số chuyên nghiệp được thiết kế cho các chuyên gia điều tra làm việc với hệ thống macOS hiện đại (10.13+) nơi mà việc thu thập vật lý truyền thống gặp khó khăn do mã hóa FileVault 2 trên các thiết bị Apple Silicon và T2 Security Chip.

### ✨ Tính năng chính

- **🗂️ Phân tích FSEvents**: Phân tích sự kiện hệ thống tệp tin (định dạng v1, v2/DLS, và **v3** - hỗ trợ macOS Sequoia 15.x)
- **📋 Thuộc tính mở rộng**: Trích xuất và giải mã cờ cách ly, nguồn tải xuống, metadata tùy chỉnh
- **⚡ Chấm điểm ưu tiên**: Tự động ưu tiên các sự kiện đáng ngờ với trọng số tùy chỉnh
- **🔍 Phát hiện mẫu tấn công**: Nhận diện 5 loại mẫu tấn công:
  - Hoạt động mã hóa ransomware
  - Nỗ lực đánh cắp dữ liệu
  - Cài đặt cơ chế tồn tại (persistence)
  - Thực thi script đáng ngờ
  - Truy cập thông tin đăng nhập
- **📊 Tạo Timeline**: Tạo dòng thời gian theo trình tự với nhóm sự kiện liên quan
- **📈 Báo cáo tương tác**: Nhiều định dạng (CSV, JSON, HTML) với trực quan hóa
- **🔐 Đảm bảo tính pháp lý**: Xác minh SHA-256, ghi log chuỗi giám sát, chế độ chỉ đọc
- **🔄 Tự động nhận diện**: Tự động phát hiện và phân tích định dạng FSEvents v1/v2/v3

### 🎯 Trường hợp sử dụng

- **Ứng phó sự cố**: Phân loại nhanh hoạt động hệ thống
- **Phân tích Malware**: Theo dõi hoạt động tệp tin độc hại
- **Điều tra vi phạm dữ liệu**: Xác định mẫu đánh cắp dữ liệu
- **Tái tạo hoạt động người dùng**: Timeline các hành động người dùng
- **Kiểm toán tuân thủ**: Ghi chép thay đổi hệ thống tệp tin

### 📦 Yêu cầu

- **Hệ điều hành**: macOS 10.13 (High Sierra) trở lên (bao gồm macOS Sequoia 15.x)
- **Python**: 3.9+
- **Quyền truy cập**: Root/Quản trị viên (chỉ cần khi thu thập FSEvents)
- **Hệ thống tệp tin**: APFS (mặc định trên macOS hiện đại)
- **Dependencies**: Liệt kê trong `requirements.txt` (tự động cài đặt)

### 🚀 Bắt đầu nhanh

#### Cài đặt

```bash
# Clone repository
git clone https://github.com/yourusername/mfaa.git
cd mfaa

# Tạo môi trường ảo
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt mFAA
pip install -e .

# Xác minh cài đặt
mfaa --version
```

#### Sử dụng cơ bản

```bash
# Phương pháp 1: Phân tích đầy đủ với sudo (thu thập + phân tích)
sudo python3 -m mfaa.cli analyze --volume / --output ./analysis --format html

# Phương pháp 2: Phân tích nhanh (sử dụng dữ liệu đã thu thập - không cần sudo)
python3 scripts/generate_forensic_report.py

# Mở báo cáo HTML tương tác
open ./output/forensic_reports/forensic_analysis.html
open ./output/forensic_reports/executive_summary.html
```

#### Sử dụng nâng cao

```bash
# Quét các artifact có sẵn (không thu thập - không cần sudo)
python3 -m mfaa.cli gather --volume / --output artifact_scan.json

# Thu thập chỉ FSEvents (cần sudo)
sudo python3 -m mfaa.cli collect --volume / --output-dir ./collected

# Phân tích dữ liệu đã thu thập (không cần sudo)
python3 -m mfaa.cli parse_cmd ./collected/.fseventsd --output parsed.json

# Tạo báo cáo từ dữ liệu đã phân tích
python3 -m mfaa.cli report_cmd parsed.json --format html --output ./reports

# Lọc chỉ các sự kiện ưu tiên cao
python3 -m mfaa.cli analyze --output ./analysis --min-priority 70 --format all
```

#### Sử dụng Docker

```bash
# Build Docker image
docker-compose build

# Chạy phân tích trong container
docker-compose run --rm mfaa analyze --volume /host --output /output
```

### 📖 Tài liệu

#### Tài liệu người dùng
- **[Bắt đầu](docs/en/user-guide/getting-started.md)** - Cài đặt và sử dụng cơ bản
- **[Tham chiếu lệnh](docs/en/user-guide/command-reference.md)** - Tài liệu CLI đầy đủ
- **[Hướng dẫn cấu hình](docs/en/configuration/configuration-guide.md)** - Tùy chỉnh hành vi và trọng số

#### Tài liệu kỹ thuật
- **[Yêu cầu nghiệp vụ](docs/en/specification/business-requirements.md)** - Đặc tả BRD đầy đủ
- **[Tóm tắt dự án](docs/en/specification/project-summary.md)** - Kiến trúc và thiết kế
- **[Đánh giá độ trưởng thành](docs/en/assessment/maturity-assessment.md)** - Chỉ số chất lượng (90/100)

#### Phát triển
- **[Lộ trình cải tiến](docs/en/development/improvement-roadmap.md)** - Cải tiến tương lai
- **[Tóm tắt sửa lỗi test](docs/en/assessment/test-fixes-summary.md)** - Cải tiến gần đây
- **[Nhật ký thay đổi](docs/en/development/changelog.md)** - Lịch sử phiên bản

### 🆕 Hỗ trợ FSEvents v3 (macOS Sequoia 15.x)

**Mới tháng 11/2025:** Hỗ trợ đầy đủ định dạng FSEvents v3 của macOS Sequoia!

#### Tính năng mới
- ✅ **Tự động nhận diện** định dạng FSEvents v1/v2/v3
- ✅ **Phân tích định dạng nhị phân** với header `3SLD`
- ✅ **4.8+ triệu sự kiện** được phân tích thành công từ hệ thống test
- ✅ **Không cần cấu hình** - hoạt động tự động

#### Đã kiểm thử trên
- **macOS Sequoia 15.6.1** (Apple Silicon)
- **2,115 file FSEvents** được phân tích
- **Tỉ lệ thành công 100%**

#### Kết quả mẫu
```bash
$ python3 scripts/generate_forensic_report.py
✓ Đã phân tích 100,000 sự kiện từ 37 file
✓ Timeline được tạo với 100,000 mục
✓ Báo cáo: HTML (132 MB), JSON (39 MB), CSV (14 MB)
```

Xem [`FORENSIC_INVESTIGATION_REPORT.md`](FORENSIC_INVESTIGATION_REPORT.md) để biết kết quả phân tích chi tiết.

### 🏗️ Kiến trúc

```
mfaa/
├── collector/          # Thu thập FSEvents và xattr
├── parser/             # Phân tích FSEvents (v1, v2/DLS, v3)
│   ├── fsevents_parser.py  # Tự động nhận diện v1/v2/v3
├── analyzer/           # Chấm điểm ưu tiên và phát hiện mẫu
├── timeline/           # Tạo timeline và nhóm sự kiện
├── reporter/           # Tạo báo cáo đa định dạng
├── cli/                # Giao diện dòng lệnh
└── models.py           # Cấu trúc dữ liệu
```

### 📊 Trạng thái dự án

| Chỉ số | Trạng thái | Ghi chú |
|--------|------------|---------|
| **Điểm trưởng thành** | 90/100 | Sẵn sàng production |
| **Tỉ lệ test pass** | 93.0% (170/183) | Cải thiện từ 75% |
| **Coverage** | 57% | Mục tiêu: 80% |
| **Modules hoàn thành** | 6/6 (100%) | Tất cả tính năng đã triển khai |
| **Tài liệu** | Đầy đủ | English + Tiếng Việt |

### 🔬 Kiểm thử

```bash
# Chạy tất cả tests
source .venv/bin/activate
pytest tests/ -v --cov=mfaa --cov-report=html

# Chạy test suite cụ thể
pytest tests/test_timeline_generator.py -v

# Xem báo cáo coverage
open htmlcov/index.html
```

### 🤝 Đóng góp

Chúng tôi hoan nghênh đóng góp! Vui lòng xem hướng dẫn đóng góp.

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/tinh-nang-tuyet-voi`)
3. Commit thay đổi (`git commit -m 'Thêm tính năng tuyệt vời'`)
4. Push lên branch (`git push origin feature/tinh-nang-tuyet-voi`)
5. Mở Pull Request

### 📝 Giấy phép

Dự án này được cấp phép theo MIT License - xem file [LICENSE](LICENSE) để biết chi tiết.

### 🙏 Cảm ơn

- Tài liệu định dạng FSEvents từ Apple Developer
- Cộng đồng điều tra số cho việc kiểm thử và phản hồi

### 📧 Liên hệ

- **Issues**: [GitHub Issues](https://github.com/yourusername/mfaa/issues)
- **Thảo luận**: [GitHub Discussions](https://github.com/yourusername/mfaa/discussions)

---

<div align="center">

**Made with ❤️ for the Digital Forensics Community**

[⬆ Back to top](#mfaa---macos-forensics-artifacts-analyzer)

</div>
