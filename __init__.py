#!/usr/bin/env python3
"""
Batch Image to PDF/EPUB/CBZ Converter
GUI and CLI modes with multi-threaded conversion and image resizing
"""

import os
import re
import sys
import argparse
import zipfile
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

# Optional EPUB
try:
    from ebooklib import epub

    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}

WIDTH_PRESETS = {
    "Auto (largest)": -2,
    "Auto (smallest)": 0,
    "600px": 600,
    "800px": 800,
    "1000px": 1000,
    "1200px": 1200,
    "1600px": 1600,
    "Original": -1
}


def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def find_images(folder):
    images = []
    try:
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                full_path = os.path.join(folder, f)
                if os.path.isfile(full_path):
                    images.append(full_path)
    except Exception:
        pass
    images.sort(key=lambda p: natural_sort_key(os.path.basename(p)))
    return images


def scan_subfolders(source):
    results = []
    for dirpath, _, _ in os.walk(source):
        images = find_images(dirpath)
        if images:
            name = os.path.basename(dirpath) if dirpath != source else os.path.basename(source)
            results.append((dirpath, images, name))
    return results


def get_unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base} ({i}){ext}"):
        i += 1
    return f"{base} ({i}){ext}"


def get_image_dimensions(path):
    """Get image dimensions without fully loading it."""
    try:
        with Image.open(path) as img:
            return img.width, img.height
    except Exception:
        return None, None


def analyze_folder_widths(images):
    """Get min, max, and all widths from images."""
    widths = []
    for p in images:
        w, _ = get_image_dimensions(p)
        if w:
            widths.append(w)
    if not widths:
        return None, None, []
    return min(widths), max(widths), widths


def get_target_width(images, width_setting):
    """
    Determine target width.
    -2 = Auto largest
    -1 = Original (no resize)
     0 = Auto smallest
    >0 = Fixed width
    """
    if width_setting == -1:
        return None

    if width_setting == 0:
        min_w, _, _ = analyze_folder_widths(images)
        return min_w

    if width_setting == -2:
        _, max_w, _ = analyze_folder_widths(images)
        return max_w

    return width_setting


def load_and_resize_image(path, target_width):
    """Load image and resize to target width."""
    try:
        img = Image.open(path)
        img.load()  # Force load

        # Resize if needed
        if target_width and target_width > 0 and img.width != target_width:
            ratio = target_width / img.width
            new_height = max(1, int(img.height * ratio))
            new_width = max(1, target_width)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img
    except Exception as e:
        raise ValueError(f"Failed to load {os.path.basename(path)}: {e}")


def convert_image_to_rgb(img):
    """Convert image to RGB, handling transparency."""
    if img.mode == 'RGB':
        return img
    if img.mode == 'RGBA' or img.mode == 'P':
        if img.mode == 'P':
            img = img.convert('RGBA')
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img)
        return background
    return img.convert('RGB')


def convert_to_pdf(images, output_path, target_width):
    """Convert images to PDF."""
    img_list = []
    errors = []

    for p in images:
        try:
            img = load_and_resize_image(p, target_width)
            img = convert_image_to_rgb(img)
            img_list.append(img)
        except Exception as e:
            errors.append(str(e))

    if not img_list:
        raise ValueError(f"No valid images. Errors: {'; '.join(errors[:3])}")

    img_list[0].save(
        output_path, "PDF",
        resolution=100.0,
        save_all=True,
        append_images=img_list[1:]
    )

    for img in img_list:
        try:
            img.close()
        except:
            pass

    return len(img_list), len(errors)


def convert_to_cbz(images, output_path, target_width):
    """Convert images to CBZ."""
    count = 0
    errors = []

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as zf:
        for i, p in enumerate(images):
            try:
                img = load_and_resize_image(p, target_width)

                buf = io.BytesIO()
                if img.mode in ('RGBA', 'P'):
                    img.save(buf, format='PNG', optimize=False)
                    ext = 'png'
                else:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(buf, format='JPEG', quality=90)
                    ext = 'jpg'

                buf.seek(0)
                zf.writestr(f"{i + 1:04d}.{ext}", buf.read())
                count += 1
                img.close()
            except Exception as e:
                errors.append(str(e))

    if count == 0:
        os.remove(output_path)
        raise ValueError(f"No valid images. Errors: {'; '.join(errors[:3])}")

    return count, len(errors)


def convert_to_epub(images, output_path, title, target_width):
    """Convert images to EPUB."""
    if not EPUB_AVAILABLE:
        raise ImportError("ebooklib not installed")

    book = epub.EpubBook()
    book.set_identifier(f'id_{hash(title)}_{hash(output_path)}')
    book.set_title(title)
    book.set_language('en')
    book.add_author('Batch Converter')

    css_content = '''
    @page { margin: 0; padding: 0; }
    body { margin: 0; padding: 0; }
    .imgpage { width: 100%; height: 100%; text-align: center; }
    .imgpage img { max-width: 100%; max-height: 100%; }
    '''
    css = epub.EpubItem(
        uid="style",
        file_name="Styles/style.css",
        media_type="text/css",
        content=css_content.encode('utf-8')
    )
    book.add_item(css)

    chapters = []
    count = 0
    errors = []

    for i, p in enumerate(images):
        try:
            img = load_and_resize_image(p, target_width)

            buf = io.BytesIO()
            if img.mode in ('RGBA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                img.save(buf, format='PNG', optimize=False)
                ext = 'png'
                mime = 'image/png'
            else:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(buf, format='JPEG', quality=90)
                ext = 'jpg'
                mime = 'image/jpeg'

            buf.seek(0)
            img_data = buf.read()

            if not img_data:
                raise ValueError("Empty image data")

            img_filename = f"Images/page_{i + 1:04d}.{ext}"
            img_item = epub.EpubItem(
                uid=f'image_{i}',
                file_name=img_filename,
                media_type=mime,
                content=img_data
            )
            book.add_item(img_item)

            ch_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Page {i + 1}</title>
    <link rel="stylesheet" type="text/css" href="../Styles/style.css"/>
</head>
<body>
    <div class="imgpage">
        <img src="../{img_filename}" alt="Page {i + 1}"/>
    </div>
</body>
</html>'''

            chapter = epub.EpubHtml(
                title=f'Page {i + 1}',
                file_name=f'Text/page_{i + 1:04d}.xhtml',
                lang='en'
            )
            chapter.content = ch_content.encode('utf-8')
            chapter.add_item(css)
            book.add_item(chapter)
            chapters.append(chapter)

            count += 1
            img.close()

        except Exception as e:
            errors.append(f"{os.path.basename(p)}: {e}")

    if not chapters:
        raise ValueError(f"No valid images for EPUB. Errors: {'; '.join(errors[:3])}")

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters

    epub.write_epub(output_path, book, {})

    # Verify file was created and has content
    if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
        raise ValueError("EPUB file creation failed")

    return count, len(errors)


def convert_folder(folder_path, images, name, output_dir, fmt, width_setting):
    """Convert a single folder."""
    ext = fmt.lower()
    out_path = get_unique_path(os.path.join(output_dir, f"{name}.{ext}"))

    try:
        target_width = get_target_width(images, width_setting)

        if fmt == "PDF":
            count, errs = convert_to_pdf(images, out_path, target_width)
        elif fmt == "CBZ":
            count, errs = convert_to_cbz(images, out_path, target_width)
        elif fmt == "EPUB":
            count, errs = convert_to_epub(images, out_path, name, target_width)
        else:
            raise ValueError(f"Unknown format: {fmt}")

        size_kb = os.path.getsize(out_path) / 1024
        if size_kb > 1024:
            size_str = f"{size_kb / 1024:.1f}MB"
        else:
            size_str = f"{size_kb:.0f}KB"

        width_str = f"w:{target_width}" if target_width else "orig"
        detail = f"{count}pg {width_str} {size_str}"

        return (name, True, os.path.basename(out_path), detail)

    except Exception as e:
        # Clean up partial file
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except:
                pass
        return (name, False, str(e)[:50], "")


# ══════════════════════════════════════════════════════════════════════════════
# CLI MODE
# ══════════════════════════════════════════════════════════════════════════════

def run_cli(args):
    source = os.path.abspath(args.source)
    output_base = os.path.abspath(args.output)
    fmt = args.format.upper()
    workers = args.workers
    width = args.width

    if fmt == "EPUB" and not EPUB_AVAILABLE:
        print("Error: EPUB requires ebooklib. Run: pip install ebooklib")
        sys.exit(1)

    if not os.path.isdir(source):
        print(f"Error: Source not found: {source}")
        sys.exit(1)

    output_dir = os.path.join(output_base, os.path.basename(source))
    os.makedirs(output_dir, exist_ok=True)

    width_name = {-2: "Auto (largest)", -1: "Original", 0: "Auto (smallest)"}.get(width, f"{width}px")

    print(f"Source:  {source}")
    print(f"Output:  {output_dir}")
    print(f"Format:  {fmt}")
    print(f"Width:   {width_name}")
    print(f"Workers: {workers}")
    print("-" * 50)

    folders = scan_subfolders(source)

    if not folders:
        print("No folders with images found.")
        sys.exit(0)

    total_images = sum(len(imgs) for _, imgs, _ in folders)
    print(f"Found {len(folders)} folders, {total_images} images")
    print("-" * 50)

    success = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(convert_folder, fp, imgs, name, output_dir, fmt, width): name
            for fp, imgs, name in folders
        }

        for future in as_completed(futures):
            name, ok, msg, details = future.result()
            if ok:
                print(f"  ✓ {msg} ({details})")
                success += 1
            else:
                print(f"  ✗ {name}: {msg}")
                failed += 1

    print("-" * 50)
    print(f"Done: {success} success, {failed} failed")


# ══════════════════════════════════════════════════════════════════════════════
# GUI MODE
# ══════════════════════════════════════════════════════════════════════════════

def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    import threading

    class App:
        def __init__(self, root):
            self.root = root
            self.root.title("Batch Image Converter")
            self.root.geometry("660x540")
            self.root.configure(bg="#f5f5f5")

            self.source = tk.StringVar()
            self.output = tk.StringVar()
            self.fmt = tk.StringVar(value="PDF")
            self.workers = tk.IntVar(value=min(os.cpu_count() or 4, 8))
            self.width_choice = tk.StringVar(value="Auto (largest)")
            self.custom_width = tk.IntVar(value=1200)
            self.folders = []
            self.converting = False

            self.root.bind("<Control-s>", lambda e: self.start())
            self.root.bind("<Control-S>", lambda e: self.start())

            self._build_ui()

        def _build_ui(self):
            pad = {'padx': 12, 'pady': 5}
            bg = "#f5f5f5"

            # Source
            tk.Label(self.root, text="Source Folder:", bg=bg, font=("Segoe UI", 10)).pack(anchor="w", **pad)
            f1 = tk.Frame(self.root, bg=bg)
            f1.pack(fill="x", padx=12, pady=2)
            tk.Entry(f1, textvariable=self.source, font=("Consolas", 10)).pack(side="left", fill="x", expand=True)
            tk.Button(f1, text="Browse", command=self._browse_src, width=8).pack(side="right", padx=(8, 0))

            # Output
            tk.Label(self.root, text="Output Folder:", bg=bg, font=("Segoe UI", 10)).pack(anchor="w", **pad)
            f2 = tk.Frame(self.root, bg=bg)
            f2.pack(fill="x", padx=12, pady=2)
            tk.Entry(f2, textvariable=self.output, font=("Consolas", 10)).pack(side="left", fill="x", expand=True)
            tk.Button(f2, text="Browse", command=self._browse_out, width=8).pack(side="right", padx=(8, 0))

            # Format + Workers
            f3 = tk.Frame(self.root, bg=bg)
            f3.pack(fill="x", padx=12, pady=8)

            tk.Label(f3, text="Format:", bg=bg, font=("Segoe UI", 10)).pack(side="left")
            for fmt in ["PDF", "CBZ", "EPUB"]:
                state = "normal" if fmt != "EPUB" or EPUB_AVAILABLE else "disabled"
                tk.Radiobutton(f3, text=fmt, variable=self.fmt, value=fmt,
                               bg=bg, font=("Segoe UI", 10), state=state).pack(side="left", padx=4)

            tk.Label(f3, text="Workers:", bg=bg, font=("Segoe UI", 10)).pack(side="left", padx=(20, 5))
            tk.Spinbox(f3, from_=1, to=32, textvariable=self.workers, width=4,
                       font=("Segoe UI", 10)).pack(side="left")

            # Width
            f4 = tk.Frame(self.root, bg=bg)
            f4.pack(fill="x", padx=12, pady=4)

            tk.Label(f4, text="Width:", bg=bg, font=("Segoe UI", 10)).pack(side="left")
            self.width_combo = ttk.Combobox(
                f4, textvariable=self.width_choice,
                values=list(WIDTH_PRESETS.keys()) + ["Custom"],
                state="readonly", width=14, font=("Segoe UI", 10)
            )
            self.width_combo.pack(side="left", padx=6)
            self.width_combo.bind("<<ComboboxSelected>>", self._on_width_change)

            tk.Label(f4, text="Custom:", bg=bg, font=("Segoe UI", 10)).pack(side="left", padx=(12, 4))
            self.custom_spin = tk.Spinbox(
                f4, from_=100, to=4000, textvariable=self.custom_width,
                width=6, font=("Segoe UI", 10), state="disabled"
            )
            self.custom_spin.pack(side="left")
            tk.Label(f4, text="px", bg=bg, font=("Segoe UI", 10)).pack(side="left", padx=2)

            # Width info
            self.width_info = tk.Label(
                self.root,
                text="↑ Largest: Scale all images to the widest one found",
                bg=bg, fg="#555", font=("Segoe UI", 9)
            )
            self.width_info.pack(anchor="w", padx=12)

            # Buttons
            f5 = tk.Frame(self.root, bg=bg)
            f5.pack(fill="x", padx=12, pady=8)

            tk.Button(f5, text="Scan", command=self._scan, width=10,
                      font=("Segoe UI", 10)).pack(side="left")
            self.convert_btn = tk.Button(
                f5, text="Convert (Ctrl+S)", command=self.start,
                width=14, font=("Segoe UI", 10, "bold")
            )
            self.convert_btn.pack(side="left", padx=10)
            tk.Button(f5, text="Clear", command=self._clear, width=8,
                      font=("Segoe UI", 10)).pack(side="left")

            # Tree
            f6 = tk.Frame(self.root)
            f6.pack(fill="both", expand=True, padx=12, pady=4)

            style = ttk.Style()
            style.configure("Treeview", font=("Consolas", 9), rowheight=22)
            style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

            cols = ("folder", "info", "status")
            self.tree = ttk.Treeview(f6, columns=cols, show="headings", height=10)
            self.tree.heading("folder", text="Folder")
            self.tree.heading("info", text="Images / Width")
            self.tree.heading("status", text="Status")
            self.tree.column("folder", width=200)
            self.tree.column("info", width=120, anchor="center")
            self.tree.column("status", width=280)

            sb = ttk.Scrollbar(f6, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=sb.set)
            self.tree.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")

            # Progress
            self.progress = ttk.Progressbar(self.root, mode="determinate")
            self.progress.pack(fill="x", padx=12, pady=6)

            self.status = tk.Label(
                self.root, text="Select folders and click Scan",
                bg=bg, font=("Segoe UI", 10)
            )
            self.status.pack(pady=4)

        def _on_width_change(self, event=None):
            choice = self.width_choice.get()
            if choice == "Custom":
                self.custom_spin.config(state="normal")
                self.width_info.config(text="Custom: Resize all images to specified width")
            else:
                self.custom_spin.config(state="disabled")
                info_map = {
                    "Auto (largest)": "↑ Largest: Scale all images to the widest one found",
                    "Auto (smallest)": "↓ Smallest: Scale all images to the narrowest one found",
                    "Original": "Original: No resizing, keep original dimensions",
                }
                self.width_info.config(
                    text=info_map.get(choice, f"Fixed: Resize all images to {WIDTH_PRESETS.get(choice, 800)}px")
                )

        def _get_width_setting(self):
            choice = self.width_choice.get()
            if choice == "Custom":
                return self.custom_width.get()
            return WIDTH_PRESETS.get(choice, -2)

        def _browse_src(self):
            p = filedialog.askdirectory(title="Select Source Folder")
            if p:
                self.source.set(p)

        def _browse_out(self):
            p = filedialog.askdirectory(title="Select Output Folder")
            if p:
                self.output.set(p)

        def _clear(self):
            self.tree.delete(*self.tree.get_children())
            self.folders = []
            self.progress["value"] = 0
            self.status.config(text="Cleared")

        def _scan(self):
            src = self.source.get().strip()
            if not src or not os.path.isdir(src):
                messagebox.showwarning("Error", "Select a valid source folder")
                return

            self.status.config(text="Scanning...")
            self.root.update()

            self.tree.delete(*self.tree.get_children())
            self.folders = scan_subfolders(src)

            for fp, imgs, name in self.folders:
                min_w, max_w, _ = analyze_folder_widths(imgs)
                if min_w and max_w:
                    if min_w == max_w:
                        info = f"{len(imgs)} img, {min_w}px"
                    else:
                        info = f"{len(imgs)} img, {min_w}-{max_w}px"
                else:
                    info = f"{len(imgs)} img"

                self.tree.insert("", "end", values=(name, info, "Ready"))

            total = sum(len(imgs) for _, imgs, _ in self.folders)
            self.status.config(text=f"Found {len(self.folders)} folders, {total} images")

        def start(self):
            if self.converting:
                return
            if not self.folders:
                messagebox.showwarning("Error", "Click Scan first")
                return

            src = self.source.get().strip()
            out = self.output.get().strip()
            if not out:
                messagebox.showwarning("Error", "Select output folder")
                return

            fmt = self.fmt.get()
            if fmt == "EPUB" and not EPUB_AVAILABLE:
                messagebox.showerror("Error", "EPUB requires: pip install ebooklib")
                return

            output_dir = os.path.join(out, os.path.basename(src))
            os.makedirs(output_dir, exist_ok=True)

            width_setting = self._get_width_setting()

            self.converting = True
            self.convert_btn.config(state="disabled")
            self.progress["value"] = 0
            self.progress["maximum"] = len(self.folders)

            # Reset status column
            for item in self.tree.get_children():
                self.tree.set(item, "status", "Pending...")

            threading.Thread(
                target=self._convert_all,
                args=(output_dir, fmt, width_setting),
                daemon=True
            ).start()

        def _convert_all(self, output_dir, fmt, width_setting):
            workers = self.workers.get()
            success = 0
            failed = 0
            items = list(self.tree.get_children())

            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_map = {}
                for i, (fp, imgs, name) in enumerate(self.folders):
                    f = executor.submit(convert_folder, fp, imgs, name, output_dir, fmt, width_setting)
                    future_map[f] = i

                for future in as_completed(future_map):
                    idx = future_map[future]
                    row_id = items[idx]
                    name, ok, msg, details = future.result()

                    if ok:
                        status = f"✓ {msg} ({details})"
                        self.root.after(0, lambda r=row_id, s=status: self.tree.set(r, "status", s))
                        success += 1
                    else:
                        status = f"✗ {msg}"
                        self.root.after(0, lambda r=row_id, s=status: self.tree.set(r, "status", s))
                        failed += 1

                    self.root.after(0, lambda v=success + failed: self._update_progress(v))

            self.root.after(0, lambda: self._done(success, failed, output_dir))

        def _update_progress(self, value):
            self.progress["value"] = value

        def _done(self, success, failed, output_dir):
            self.converting = False
            self.convert_btn.config(state="normal")
            self.status.config(text=f"Done: {success} success, {failed} failed")

            if failed > 0:
                messagebox.showwarning(
                    "Done with Errors",
                    f"Converted: {success}\nFailed: {failed}\n\nOutput:\n{output_dir}"
                )
            else:
                messagebox.showinfo(
                    "Done",
                    f"Converted: {success} files\n\nOutput:\n{output_dir}"
                )

    root = tk.Tk()
    App(root)
    root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Batch convert image folders to PDF/EPUB/CBZ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Width options:
  -2   = Auto largest (scale up to widest image)
  -1   = Original (no resize)
   0   = Auto smallest (scale down to narrowest)
  >0   = Fixed width in pixels

Examples:
  python converter.py
  python converter.py -s ./Manga -o ./Out -f pdf
  python converter.py -s ./Manga -o ./Out -f epub --width -2
  python converter.py -s ./Manga -o ./Out -f cbz --width 1200 -w 8
        """
    )
    parser.add_argument("-s", "--source", help="Source folder")
    parser.add_argument("-o", "--output", help="Output folder")
    parser.add_argument("-f", "--format", choices=["pdf", "epub", "cbz"], default="pdf")
    parser.add_argument("-w", "--workers", type=int, default=min(os.cpu_count() or 4, 8))
    parser.add_argument("--width", type=int, default=-2,
                        help="Width: -2=auto largest, -1=original, 0=auto smallest, >0=fixed")
    parser.add_argument("--gui", action="store_true", help="Force GUI mode")

    args = parser.parse_args()

    if args.source and args.output and not args.gui:
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
