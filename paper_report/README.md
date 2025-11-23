# Báo cáo Đề tài: macOS Forensics Artifacts Analyzer (mFAA)

## Thông tin môn học

| Thông tin | Chi tiết |
|-----------|----------|
| **Môn học** | Điều tra số (Digital Forensics) |
| **Lớp** | CHAT3P |
| **Học kỳ** | HK1 2025 |
| **Trường** | Học viện Kỹ thuật Mật mã |
| **Giảng viên hướng dẫn** | PGS.TS. Đặng Trần Khánh |

---

## Thông tin nhóm thực hiện

### Nhóm 6

| STT | Họ và tên | Mã sinh viên | Vai trò |
|-----|-----------|--------------|---------|
| 1 | Nguyễn Lê Quốc Anh | CHAT3P01 | Trưởng nhóm |
| 2 | Hồ Văn Nguyên | CHAT1137 | Thành viên |

---

## Thông tin đề tài

### Tên đề tài
**Phát triển công cụ thu thập và phân tích artifacts trên hệ điều hành macOS phục vụ điều tra số**

### Tên tiếng Anh
**mFAA - macOS Forensics Artifacts Analyzer**

### Phiên bản
- **Báo cáo:** v2.0 (Cập nhật: 23/11/2025)
- **Công cụ mFAA:** v1.0

---

## Tóm tắt đề tài

### Bối cảnh và vấn đề

Các thiết bị macOS hiện đại (Apple Silicon M1/M2/M3 và Intel với T2 Security Chip) sử dụng mã hóa FileVault 2 tích hợp sâu vào phần cứng với Secure Enclave, khiến việc thu thập bằng chứng số theo phương pháp truyền thống (physical/dead acquisition) **không khả thi**. Điều này đặt ra thách thức lớn cho điều tra số khi:

- Encryption keys được bảo vệ trong phần cứng
- DMA protection ngăn chặn memory acquisition
- Signed System Volume (SSV) bảo vệ system files

### Giải pháp đề xuất

Phát triển **mFAA (macOS Forensics Artifacts Analyzer)** - công cụ điều tra số mã nguồn mở cho **live acquisition** trên macOS, tập trung vào:

1. **FSEvents (File System Events):** Ghi lại mọi thay đổi trên file system ở kernel level
2. **Extended Attributes:** Metadata bổ sung như quarantine info, download sources

### Đóng góp chính

#### Về mặt khoa học
- Tài liệu hóa **FSEvents v3** (macOS Sequoia 15.x) - định dạng mới chưa được công bố
- Thuật toán **Priority Scoring** đa yếu tố cho phân loại sự kiện
- Framework phát hiện 5 loại **pattern tấn công**

#### Về mặt kỹ thuật
- Kiến trúc **modular** với 6 modules: Collection, Parser, Analyzer, Timeline, Reporter, CLI
- Hỗ trợ **FSEvents v1/v2/v3** với auto-detection
- Hiệu năng: **117,000 events/giây**, xử lý thành công **4.8M+ events**
- **93% test pass rate** (170/183 tests)

#### Về mặt thực tiễn
- Giảm **80% thời gian** phân tích thủ công
- Xuất báo cáo **CSV/JSON/HTML** tương tác
- **Open-source** (MIT License)

---

## Nội dung báo cáo

### Cấu trúc chương

| Chương | Tiêu đề | Nội dung chính |
|--------|---------|----------------|
| 1 | Giới thiệu | Bối cảnh, mục tiêu, phạm vi nghiên cứu |
| 2 | Cơ sở lý thuyết | **FSEvents v1/v2/v3**, Extended Attributes, Live Acquisition |
| 3 | Tổng quan về FSEvents | Kiến trúc và cơ chế hoạt động |
| 4 | Phương pháp nghiên cứu | Agile methodology, yêu cầu, kiến trúc |
| 5 | Thiết kế và cài đặt | Module design, algorithms, implementation |
| 6 | Kết quả và đánh giá | Benchmarks, test cases, so sánh công cụ |
| 7 | Kết luận | Đóng góp, hạn chế, hướng phát triển |

### Điểm nổi bật của báo cáo v2.0

**Chapter 2 đã được refactor** để tập trung vào cấu trúc FSEvents:

- **FSEvents v1:** Page-based, uncompressed, 12-byte header
- **FSEvents v2/DLS:** Gzip compressed, headers 1SLD/2SLD/DLS2, 16-byte page header
- **FSEvents v3:** Header 3SLD, improved compression (~30% better), backward-compatible

Bao gồm:
- Binary structure diagrams (TikZ)
- C struct definitions
- Python parsing implementations
- Event flags reference table
- Timestamp conversion algorithms

---

## Files trong thư mục

| File | Mô tả |
|------|-------|
| `CHAT3P_G6_DigitalForensics_FinalReport.pdf` | Báo cáo đầy đủ (108 trang) |
| `DF_Final.html` | Slide trình bày |
| `README.md` | File này |

---

## Cách compile báo cáo

### Sử dụng Docker (khuyến nghị)

```bash
# Từ thư mục gốc của project
./scripts/compile_latex_docker.sh
```

### Sử dụng MacTeX

```bash
# Cài đặt MacTeX
brew install --cask mactex

# Compile
python scripts/compile_latex_report.py
```

### Sử dụng Overleaf

Upload thư mục `reports/overleaf/` lên [Overleaf](https://www.overleaf.com) và compile online.

---

## Từ khóa

`Digital Forensics` · `macOS Forensics` · `FSEvents` · `Live Acquisition` · `APFS` · `Extended Attributes` · `Timeline Analysis` · `Incident Response` · `Pattern Detection` · `Apple Silicon` · `FileVault 2`

---

## Liên hệ

- **Repository:** https://github.com/H4niz/MOSDFTools
- **Email:** [Contact via GitHub]

---

*Cập nhật lần cuối: 23/11/2025*
