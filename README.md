Here's a comprehensive README.md for your Batch Image Converter:

```markdown
# Batch Image Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)

A powerful, multi-threaded tool for converting collections of images into PDF, EPUB, or CBZ formats with automatic resizing and intelligent width normalization.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [GUI Mode](#gui-mode)
  - [CLI Mode](#cli-mode)
- [Width Options](#width-options)
- [Formats](#formats)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Technical Details](#technical-details)
- [License](#license)

---

## Features

✅ **Multi-format Output**: PDF, EPUB, CBZ
✅ **Automatic Width Normalization**: Scale images to consistent sizes
✅ **Multi-threaded Processing**: Fast conversion using all CPU cores
✅ **Natural Sorting**: `page2.jpg` before `page10.jpg`
✅ **Recursive Folder Scanning**: Processes all subfolders
✅ **GUI and CLI Modes**: Choose your preferred interface
✅ **Error Handling**: Detailed error reporting
✅ **Transparency Support**: Proper handling of PNG/GIF transparency
✅ **High-Quality Resizing**: Uses LANCZOS resampling
✅ **Duplicate Protection**: Auto-renames existing files

---

## Installation

### Requirements

- Python 3.7 or higher
- Pillow library (required)
- ebooklib (optional, for EPUB support)

### Install with pip

```bash
pip install Pillow
```

For EPUB support:

```bash
pip install ebooklib
```

### Download

Clone the repository:

```bash
git clone https://github.com/yourusername/batch-image-converter.git
cd batch-image-converter
```

---

## Usage

### GUI Mode

1. Run the application:
   ```bash
   python converter.py
   ```

2. **Source Folder**: Select the folder containing your subfolders of images
3. **Output Folder**: Select where to save the converted files
4. **Format**: Choose PDF, EPUB, or CBZ
5. **Width**: Select your preferred width handling
6. **Workers**: Set the number of parallel threads (default: CPU cores)
7. Click **Scan** to preview the folders
8. Click **Convert** or press `Ctrl+S` to start conversion

#### Width Options (GUI)

| Option | Description |
|--------|-------------|
| **Auto (largest)** | Scale all images to match the widest image in each folder |
| **Auto (smallest)** | Scale all images to match the narrowest image in each folder |
| **600px, 800px, etc.** | Fixed width in pixels |
| **Original** | No resizing, keep original dimensions |
| **Custom** | Enter any specific width |

### CLI Mode

Run with command-line arguments:

```bash
python converter.py -s SOURCE -o OUTPUT -f FORMAT [OPTIONS]
```

#### Basic Example

```bash
python converter.py -s ./Manga -o ./Output -f pdf
```

#### Advanced Example

```bash
python converter.py \
  --source ./Comics \
  --output ./PDFs \
  --format cbz \
  --workers 8 \
  --width -2
```

#### CLI Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--source` | `-s` | — | Source folder containing subfolders |
| `--output` | `-o` | — | Output base folder |
| `--format` | `-f` | `pdf` | Output format (`pdf`, `epub`, `cbz`) |
| `--workers` | `-w` | CPU cores | Number of parallel threads |
| `--width` | — | `-2` | Width handling (see below) |
| `--gui` | — | — | Force GUI mode |

#### Width Options (CLI)

| Value | Description |
|-------|-------------|
| `-2` | Auto (largest) - Scale to widest image |
| `-1` | Original - No resizing |
| `0` | Auto (smallest) - Scale to narrowest image |
| `>0` | Fixed width in pixels |

---

## Width Options Explained

### Auto (largest) - `-2`

Scales all images in a folder to match the **widest** image found:

```
Folder contains:
  page1.jpg  (800px wide)
  page2.jpg  (1200px wide)  ← widest
  page3.jpg  (1000px wide)

Result:
  page1.jpg → scaled UP to 1200px
  page2.jpg → stays 1200px
  page3.jpg → scaled UP to 1200px
```

### Auto (smallest) - `0`

Scales all images in a folder to match the **narrowest** image found:

```
Folder contains:
  page1.jpg  (800px wide)  ← narrowest
  page2.jpg  (1200px wide)
  page3.jpg  (1000px wide)

Result:
  page1.jpg → stays 800px
  page2.jpg → scaled DOWN to 800px
  page3.jpg → scaled DOWN to 800px
```

### Fixed Width - `>0`

Scales all images to an exact width (e.g., `800`):

```
Folder contains:
  page1.jpg  (600px wide)
  page2.jpg  (1200px wide)
  page3.jpg  (1000px wide)

With --width 800:
  page1.jpg → scaled UP to 800px
  page2.jpg → scaled DOWN to 800px
  page3.jpg → scaled DOWN to 800px
```

### Original - `-1`

No resizing, keeps original dimensions:

```
Folder contains:
  page1.jpg  (600px wide)
  page2.jpg  (1200px wide)
  page3.jpg  (1000px wide)

Result:
  All images keep their original widths
```

---

## Formats

### PDF

- **Best for**: Universal viewing, printing
- **Features**:
  - High quality output
  - Preserves image quality
  - Good for archiving

### EPUB

- **Best for**: E-readers (Kindle, Kobo, Apple Books)
- **Features**:
  - Reflowable format
  - Works on most e-readers
  - Requires `ebooklib` (`pip install ebooklib`)

### CBZ

- **Best for**: Comic readers (CDisplayEx, Perfect Viewer, YACReader)
- **Features**:
  - Simple ZIP archive of images
  - Preserves original image quality
  - No conversion overhead

---

## Performance

The converter uses Python's `ThreadPoolExecutor` for parallel processing.

### Performance Tips

| Scenario | Recommended Workers | Notes |
|----------|---------------------|-------|
| SSD + many cores | 8-16 | Can handle more parallel operations |
| HDD | 2-4 | Disk I/O is the bottleneck |
| Low RAM | 2-4 | Each worker loads images into memory |
| Large images | 4-8 | More RAM per worker needed |
| Many small images | 8-16 | Less memory per image |

### Memory Usage

- Each worker loads and processes images independently
- For very large images, reduce worker count to avoid memory issues
- Original images are not modified - working copies are created in memory

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| EPUB option disabled | Install ebooklib: `pip install ebooklib` |
| Out of memory errors | Reduce workers with `-w 2` or use smaller width |
| Empty output files | Check for corrupted image files in source |
| Wrong image order | Rename files with zero-padding: `001.jpg`, `002.jpg` |
| Linux GUI won't open | Install tkinter: `sudo apt install python3-tk` |
| Slow conversion | Increase workers or use SSD |
| "No modules named PIL" | Install Pillow: `pip install Pillow` |

### Error Messages

The application provides detailed error messages including:
- Which specific images failed to process
- The type of error (corrupted file, unsupported format, etc.)
- Suggestions for fixing the issue

---

## Advanced Usage

### Batch Processing

Process multiple source folders in sequence:

```bash
for dir in */; do
  python converter.py -s "$dir" -o ./Output -f pdf --width -2
done
```

### Custom Widths

For specific width requirements:

```bash
# Scale to 1000px wide
python converter.py -s ./Manga -o ./Output -f pdf --width 1000

# Keep original sizes
python converter.py -s ./Manga -o ./Output -f cbz --width -1
```

### Quality Settings

The converter uses:
- **JPEG quality 90** for CBZ/EPUB
- **LANCZOS resampling** for high-quality downscaling
- **100 DPI** for PDF output

---

## Technical Details

### Image Processing

1. **Loading**: Images are loaded with PIL/Pillow
2. **Resizing**: Uses high-quality LANCZOS resampling
3. **Color Conversion**: RGBA/PNG images are composited on white background
4. **Memory Management**: Images are properly closed after processing

### File Handling

1. **Duplicate Protection**: Automatically renames files if output exists
2. **Error Recovery**: Partial files are cleaned up if conversion fails
3. **Natural Sorting**: Files are sorted alphabetically with number awareness

### Thread Safety

- Each thread processes a separate folder
- No shared state between threads
- Proper resource cleanup

---

## Output Structure

```
Source: /path/to/Comics/
├── Series1/
│   ├── page1.jpg
│   ├── page2.jpg
│   └── ...
├── Series2/
│   ├── page1.jpg
│   └── ...
└── ...

Output: /path/to/Output/
└── Comics/
    ├── Series1.pdf
    ├── Series2.pdf
    └── ...
```

Each subfolder in the source becomes a single output file named after the subfolder.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

### Feature Ideas

- Add MOBI/KF8 output format
- Implement image rotation based on EXIF
- Add margin/crop options
- Support for additional image formats
- Batch renaming before conversion
- Dark mode for GUI

---

## Changelog

### [1.0.0] - Current Version

- Added automatic width detection (largest/smallest)
- Fixed EPUB empty document issues
- Improved error handling and reporting
- Added comprehensive width options
- Enhanced GUI with width preview
- Added file size reporting
- Improved memory management

---

## Support

For questions or issues, please open an issue on GitHub.

---

## Examples

### Convert Manga to PDF with Auto Width

```bash
python converter.py -s ~/Downloads/MyManga -o ~/Documents -f pdf --width -2
```

### Convert Comics to CBZ with Fixed Width

```bash
python converter.py -s ~/Comics -o ~/CBZ -f cbz --width 1200 -w 8
```

### Convert Novels to EPUB with Original Sizes

```bash
python converter.py -s ~/Novels -o ~/Books -f epub --width -1
```

---

## Screenshots

### GUI Main Window
![GUI Main Window](screenshots/main.png)

### Width Options
![Width Options](screenshots/width.png)

### Conversion Progress
![Conversion Progress](screenshots/progress.png)

---

## Credits

- [Pillow](https://python-pillow.org/) - Python Imaging Library
- [ebooklib](https://github.com/aerkalov/ebooklib) - EPUB library
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI toolkit
```

This comprehensive README includes:

1. **Detailed feature list** explaining all capabilities
2. **Complete installation instructions** for all platforms
3. **Step-by-step usage guides** for both GUI and CLI
4. **In-depth explanation** of all width options with examples
5. **Format comparisons** with best use cases
6. **Performance tuning** advice
7. **Comprehensive troubleshooting** section
8. **Advanced usage** examples
9. **Technical details** about implementation
10. **Visual examples** of output structure
11. **License and contribution** information
12. **Changelog** and future ideas
13. **Example commands** for common use cases
14. **Screenshots** section (you would need to add actual screenshots)

The document is structured to first give a quick overview, then dive into details for those who need more information, making it accessible to both casual users and advanced users.
