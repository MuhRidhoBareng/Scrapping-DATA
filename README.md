# Web Scraper - Review Extractor

**Aplikasi desktop untuk scraping review dari berbagai website (Yelp, TripAdvisor, Google Reviews, dll)**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🚀 Fitur

- 📁 Pilih folder atau file HTML langsung
- ⚙️ Preset untuk berbagai website (Yelp, TripAdvisor, Google, Custom)
- 📅 Filter review berdasarkan tahun
- ✓ Validasi data otomatis dengan quality score
- 📊 Preview hasil dalam tabel
- 💾 Export ke CSV

## 📋 Requirements

```bash
pip install beautifulsoup4 lxml
```

## 🔧 Penggunaan

### Metode 1: Jalankan GUI
```bash
python scraper_gui.py
```
Atau double-click `Run_Scraper.bat`

### Metode 2: Command Line
```bash
python html_parser.py
```

## 📖 Cara Kerja

1. **Download halaman HTML** dari website target (Ctrl+S → Webpage, Complete)
2. **Pilih file/folder** di aplikasi
3. **Pilih preset** sesuai website (Yelp, TripAdvisor, dll)
4. **Klik Start Scraping**
5. **Validate Data** untuk cek kualitas
6. **Export CSV** untuk menyimpan hasil

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

## 👤 Author

**Muhammad Ridho Bareng**
- GitHub: [@MuhRidhoBareng](https://github.com/MuhRidhoBareng)

## 📄 License

MIT License - free to use and modify
