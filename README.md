## Batch Image To Pdf Converter


# README.md

# Batch Image Converter

Convert image folders to PDF / EPUB / CBZ with automatic width normalization.

## Install

```bash
pip install Pillow

# Optional: EPUB support
pip install ebooklib
```

## Quick Start

```bash
# GUI (default)
python converter.py

# CLI - auto scale to largest width
python converter.py -s ./Manga -o ./Output -f pdf

# CLI - fixed width
python converter.py -s ./Manga -o ./Output -f epub --width 1200
```

## Width Options

| Value | Name | Description |
|-------|------|-------------|
| `-2` | Auto (largest) | Scale ALL images to match the **widest** image |
| `-1` | Original | No resizing |
| `0` | Auto (smallest) | Scale ALL images to match the **narrowest** image |
| `>0` | Fixed | Set exact width (e.g., `800`, `1200`) |

### Example: Auto Largest

```
Folder contains:
  page1.jpg  (800px wide)
  page2.jpg  (1200px wide)  ← widest
  page3.jpg  (1000px wide)

With --width -2 (Auto largest):
  page1.jpg → scaled UP to 1200px
  page2.jpg → stays 1200px
  page3.jpg → scaled UP to 1200px

Result: All pages are 1200px wide
```

## CLI Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--source` | `-s` | — | Source folder |
| `--output` | `-o` | — | Output folder |
| `--format` | `-f` | `pdf` | `pdf`, `epub`, `cbz` |
| `--workers` | `-w` | 8 | Thread count |
| `--width` | — | `-2` | See width options above |
| `--gui` | — | — | Force GUI mode |

## CLI Examples

```bash
# Auto scale to largest (default)
python converter.py -s ./Comics -o ./PDFs -f pdf

# Auto scale to smallest
python converter.py -s ./Comics -o ./PDFs -f pdf --width 0

# Fixed 1000px width
python converter.py -s ./Comics -o ./PDFs -f cbz --width 1000

# Original sizes (no resize)
python converter.py -s ./Comics -o ./PDFs -f pdf --width -1

# 12 workers for fast SSD
python converter.py -s ./Comics -o ./PDFs -f pdf -w 12
```

## GUI Features

- Scan shows **min-max width** for each folder
- Dropdown presets: Auto Largest, Auto Smallest, fixed sizes
- Custom width input
- Progress per folder
- `Ctrl+S` to start

## Output

```
Source: /Manga/OnePiece/
Output: /Downloads/

Creates: /Downloads/OnePiece/
├── Chapter 001.pdf
├── Chapter 002.pdf
└── Chapter 003.pdf
```

## Formats

| Format | Best For |
|--------|----------|
| PDF | Universal |
| CBZ | Comic readers |
| EPUB | E-readers |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| EPUB disabled | `pip install ebooklib` |
| Out of memory | Reduce workers (`-w 2`) |
| Empty documents | Check image files aren't corrupted |
| Wrong order | Rename: `001.jpg`, `002.jpg`, etc. |
| Linux no GUI | `sudo apt install python3-tk` |

## License

MIT
```

---

## Changes Made

| Fix | Description |
|-----|-------------|
| **EPUB empty fix** | Added `img.load()` to force image loading, better error handling, file verification |
| **Auto (largest)** | New option `-2` scales all images UP to widest one found |
| **Better error messages** | Shows which images failed and why |
| **Width analysis** | Scan shows min-max width range per folder |
| **Cleanup on error** | Removes partial files if conversion fails |
| **Image data validation** | Checks buffer isn't empty before writing |
| **Default changed** | Now defaults to "Auto (largest)" which is more useful |
| **Simpler GUI** | Cleaner colors, better fonts |
