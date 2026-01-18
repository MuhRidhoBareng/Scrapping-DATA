# Web Scraper - Review Extractor

**Aplikasi desktop untuk scraping review dari berbagai website (Yelp, TripAdvisor, Google Reviews, dll)**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## 🚀 Fitur

- 📁 Pilih folder atau file HTML langsung
- 🔍 Search subfolders - cari file HTML di subfolder
- ⚙️ Preset untuk berbagai website (Yelp, TripAdvisor, Google, Custom)
- 📅 Filter review berdasarkan tahun (2019-2025)
- ✓ **Validasi data otomatis** dengan quality score
- 📊 Preview hasil dalam tabel real-time
- 💾 Export ke CSV
- 🔗 Clickable GitHub link di footer

## 📋 Requirements

```bash
pip install beautifulsoup4 lxml
```

## 🔧 Penggunaan

### Metode 1: Executable (Recommended)
Download `WebScraper.exe` dari folder `dist/` dan jalankan langsung (tidak perlu Python).

### Metode 2: Jalankan GUI dari Python
```bash
python scraper_gui.py
```
Atau double-click `Run_Scraper.bat`

### Metode 3: Command Line
```bash
python html_parser.py
```

## 📖 Cara Kerja

1. **Download halaman HTML** dari website target (Ctrl+S → Webpage, Complete)
2. **Pilih file/folder** di aplikasi (gunakan tombol "Files" atau "Folder")
3. **Pilih preset** sesuai website (Yelp, TripAdvisor, dll)
4. **Klik Start Scraping**
5. **Validate Data** untuk cek kualitas data
6. **Export CSV** untuk menyimpan hasil

## ✓ Fitur Validasi Data

Klik tombol "Validate Data" untuk mengecek:
- Empty fields check
- Rating validation (1-5)
- Date format validation
- Review text length analysis
- Duplicate detection
- **Data Quality Score (0-100)**

## 📊 Output Columns

| Column | Description |
|--------|-------------|
| username | Nama reviewer |
| from | Lokasi reviewer |
| written_date | Tanggal review |
| rating | Rating (1-5) |
| title | Judul review |
| review_text | Isi review |
| tema_pengalaman | Status Elite |
| daya_tarik_wisata | Helpful count |
| status | Elite status |
| contribution | Review/photo count |

## 📁 Struktur File

```
Scraping-DATA/
├── dist/
│   └── WebScraper.exe      # Executable (standalone)
├── scraper_gui.py          # Aplikasi desktop GUI
├── html_parser.py          # Parser untuk Yelp
├── custom_scraper.py       # Scraper universal
├── scraper_config.py       # File konfigurasi
├── Run_Scraper.bat         # Launcher Windows
├── requirements.txt        # Dependencies
└── README.md               # Dokumentasi
```

## 🖼️ Screenshot

Aplikasi menampilkan:
- Panel pemilihan file/folder
- Konfigurasi website preset
- Filter tahun
- Log output real-time
- Preview hasil dalam tabel
- Tombol validasi dan export

## 👤 Author

**Muhammad Ridho Bareng**
- GitHub: [@MuhRidhoBareng](https://github.com/MuhRidhoBareng)

## 📄 License

MIT License - free to use and modify
