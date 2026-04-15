# README.md

# 📁 Batch Folder → PDF Converter

A simple Python desktop app that converts folders of JPEG/image files into
PDF documents — one PDF per subfolder, named after the subfolder, saved to
an output folder of your choosing.


## 📸 What It Does

Given a source folder full of subfolders (each containing images), the app will:

1. Detect all subfolders recursively
2. Find all images inside each subfolder
3. Sort them **alphanumerically** (so `page2` comes before `page10`)
4. Convert each subfolder's images into a single PDF
5. Name each PDF after its subfolder
6. Save all PDFs into an output folder you choose

### Example

```
Source Folder/
├── Chapter 1/
│   ├── page1.jpg
│   ├── page2.jpg
│   └── page10.jpg
├── Chapter 2/
│   ├── img_001.jpg
│   └── img_002.png
└── Bonus/
    └── scan.jpeg
```

**Becomes:**

```
Output Folder/
├── Chapter 1.pdf
├── Chapter 2.pdf
└── Bonus.pdf
```

---

## 🖥️ Requirements

- Python **3.7+**
- [Pillow](https://pypi.org/project/Pillow/)

---

## ⚙️ Installation

**1. Clone or download this repo**

```bash
git clone https://github.com/yourname/batch-folder-pdf.git
cd batch-folder-pdf
```

**2. (Optional but recommended) Create a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install Pillow
```

---

## 🚀 Usage

```bash
python converter.py
```

### Step-by-step

| Step | Action |
|------|--------|
| **1** | Click **Browse** next to *Source Folder* and select the parent folder containing your subfolders |
| **2** | Click **Browse** next to *Output Folder* and select where you want the PDFs saved |
| **3** | Click **🔍 Scan Subfolders** to detect all subfolders and preview what will be converted |
| **4** | *(Optional)* Double-click any row in the list to preview the image order for that folder |
| **5** | Click **🔄 Convert All to PDFs** to start the batch conversion |

---

## 🗂️ Supported Image Formats

| Format | Extensions |
|--------|------------|
| JPEG | `.jpg` `.jpeg` |
| PNG | `.png` |
| Bitmap | `.bmp` |
| TIFF | `.tiff` `.tif` |
| WebP | `.webp` |

---

## ✨ Features

- **Recursive subfolder detection** — scans all nested subfolders
- **Natural alphanumeric sorting** — `page2.jpg` sorts before `page10.jpg`
- **Auto PDF naming** — PDF takes the name of its source subfolder
- **Duplicate protection** — if `Chapter 1.pdf` already exists, saves as `Chapter 1 (1).pdf`
- **Live preview** — double-click any row to see the exact image order before converting
- **Progress bar** — real-time progress with per-folder status
- **Non-blocking UI** — conversion runs in a background thread so the app stays responsive
- **Multi-format support** — handles PNG, BMP, TIFF, WebP in addition to JPEG
- **Root folder images** — images placed directly in the source folder are captured too

---

## 📁 Project Structure

```
batch-folder-pdf/
│
├── converter.py       # Main application
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## 📦 requirements.txt

```
Pillow>=10.0.0
```

---

## 🛠️ Troubleshooting

**App won't open**
- Make sure Python 3.7+ is installed: `python --version`
- Make sure Pillow is installed: `pip install Pillow`
- On Linux you may need tkinter: `sudo apt-get install python3-tk`

**No subfolders found**
- Make sure your source folder actually *contains subfolders* with images inside
- Images must be directly inside the subfolders (not deeper nested levels skipped)
- Check that your images have a supported extension (`.jpg`, `.jpeg`, `.png`, etc.)

**PDF looks wrong / images out of order**
- The app sorts by natural alphanumeric order
- Rename your files with zero-padded numbers for guaranteed order:
  `page001.jpg`, `page002.jpg`, ..., `page010.jpg`

**Conversion failed for a folder**
- The status column will show ❌ with an error snippet
- Common causes: corrupted image file, insufficient disk space, permission error
- Check the file manually and remove or replace it

**Output PDF is too large**
- The app saves at 100 DPI by default
- For smaller files, pre-resize your images before converting

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙌 Contributing

Pull requests welcome! Some ideas for improvements:

- [ ] DPI setting slider in the UI
- [ ] PDF compression options
- [ ] Drag-and-drop folder support
- [ ] Progress log export
- [ ] Page size options (A4, Letter, etc.)
- [ ] Option to flatten nested subfolders into one PDF

---

*Built with Python + Tkinter + Pillow*
```
