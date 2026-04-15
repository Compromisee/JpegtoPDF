import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import os
import re
import threading


def natural_sort_key(s):
    """Sort strings with embedded numbers naturally.
    e.g. img2.jpg comes before img10.jpg"""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', s)
    ]


class BatchFolderConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Folder → PDF Converter")
        self.root.geometry("700x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#2b2b2b")

        self.source_folder = tk.StringVar(value="")
        self.output_folder = tk.StringVar(value="")
        self.subfolders = []  # list of (subfolder_path, [image_files])
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        self.is_converting = False  # Prevent multiple conversions

        # ── Keyboard Shortcuts ────────────────────────────────────────────────
        self.root.bind("<Control-s>", self.shortcut_convert)
        self.root.bind("<Control-S>", self.shortcut_convert)  # Handle caps lock

        # ── Title ─────────────────────────────────────────────────────────────
        tk.Label(
            root, text="📁 Batch Folder → PDF",
            font=("Helvetica", 20, "bold"),
            bg="#2b2b2b", fg="#ffffff"
        ).pack(pady=(15, 5))

        tk.Label(
            root,
            text="Import a folder → each subfolder becomes a PDF (named after the subfolder)",
            font=("Helvetica", 10), bg="#2b2b2b", fg="#aaaaaa",
            wraplength=650
        ).pack(pady=(0, 10))

        # ── Source Folder ─────────────────────────────────────────────────────
        src_frame = tk.Frame(root, bg="#2b2b2b")
        src_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(src_frame, text="📂 Source Folder:",
                 font=("Helvetica", 11, "bold"), bg="#2b2b2b", fg="#ffffff"
                 ).pack(anchor="w")

        src_row = tk.Frame(src_frame, bg="#2b2b2b")
        src_row.pack(fill="x", pady=3)

        self.src_entry = tk.Entry(
            src_row, textvariable=self.source_folder,
            font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white", relief="flat",
            highlightthickness=1, highlightcolor="#007ACC"
        )
        self.src_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            src_row, text="Browse", command=self.browse_source,
            font=("Helvetica", 10), bg="#4CAF50", fg="white",
            padx=12, pady=3, relief="flat", cursor="hand2"
        ).pack(side="right")

        # ── Output Folder ─────────────────────────────────────────────────────
        out_frame = tk.Frame(root, bg="#2b2b2b")
        out_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(out_frame, text="💾 Output Folder:",
                 font=("Helvetica", 11, "bold"), bg="#2b2b2b", fg="#ffffff"
                 ).pack(anchor="w")

        out_row = tk.Frame(out_frame, bg="#2b2b2b")
        out_row.pack(fill="x", pady=3)

        self.out_entry = tk.Entry(
            out_row, textvariable=self.output_folder,
            font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white", relief="flat",
            highlightthickness=1, highlightcolor="#007ACC"
        )
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            out_row, text="Browse", command=self.browse_output,
            font=("Helvetica", 10), bg="#2196F3", fg="white",
            padx=12, pady=3, relief="flat", cursor="hand2"
        ).pack(side="right")

        # ── Scan Button ──────────────────────────────────────────────────────
        tk.Button(
            root, text="🔍 Scan Subfolders", command=self.scan_folders,
            font=("Helvetica", 12, "bold"), bg="#ff9800", fg="white",
            padx=20, pady=6, relief="flat", cursor="hand2"
        ).pack(pady=10)

        # ── Preview Tree ─────────────────────────────────────────────────────
        tree_frame = tk.Frame(root, bg="#2b2b2b")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        columns = ("subfolder", "images", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        self.tree.heading("subfolder", text="Subfolder → PDF Name")
        self.tree.heading("images", text="Images Found")
        self.tree.heading("status", text="Status")
        self.tree.column("subfolder", width=320)
        self.tree.column("images", width=100, anchor="center")
        self.tree.column("status", width=200, anchor="center")

        # Style the treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#1e1e1e",
                        foreground="#d4d4d4",
                        fieldbackground="#1e1e1e",
                        font=("Consolas", 10),
                        rowheight=24)
        style.configure("Treeview.Heading",
                        background="#333333",
                        foreground="#ffffff",
                        font=("Helvetica", 10, "bold"))
        style.map("Treeview",
                  background=[("selected", "#007ACC")],
                  foreground=[("selected", "white")])

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Info + Preview Detail ────────────────────────────────────────────
        self.info_label = tk.Label(
            root, text="No folders scanned yet.",
            font=("Helvetica", 10), bg="#2b2b2b", fg="#aaaaaa"
        )
        self.info_label.pack(pady=2)

        # Double-click to preview images in a subfolder
        self.tree.bind("<Double-1>", self.preview_subfolder)

        # ── Progress Bar ─────────────────────────────────────────────────────
        self.progress = ttk.Progressbar(root, mode="determinate", length=660)
        self.progress.pack(padx=20, pady=(5, 5))

        self.progress_label = tk.Label(
            root, text="",
            font=("Helvetica", 10), bg="#2b2b2b", fg="#ffcc00"
        )
        self.progress_label.pack()

        # ── Convert Button ───────────────────────────────────────────────────
        self.convert_btn = tk.Button(
            root, text="🔄 Convert All to PDFs (Ctrl+S)", command=self.start_conversion,
            font=("Helvetica", 14, "bold"), bg="#007ACC", fg="white",
            padx=30, pady=8, relief="flat", cursor="hand2"
        )
        self.convert_btn.pack(pady=(5, 15))

        # ── Shortcut Hint ────────────────────────────────────────────────────
        tk.Label(
            root,
            text="⌨️ Ctrl+S to start conversion",
            font=("Helvetica", 9), bg="#2b2b2b", fg="#666666"
        ).pack(side="bottom", pady=(0, 5))

    # ── Keyboard Shortcut Handler ─────────────────────────────────────────────

    def shortcut_convert(self, event=None):
        """Handle Ctrl+S keyboard shortcut."""
        if not self.is_converting:
            self.start_conversion()
        return "break"  # Prevent default behavior

    # ── Browse Dialogs ────────────────────────────────────────────────────────

    def browse_source(self):
        folder = filedialog.askdirectory(title="Select Source Folder (contains subfolders)")
        if folder:
            self.source_folder.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder for PDFs")
        if folder:
            self.output_folder.set(folder)

    # ── Scan ──────────────────────────────────────────────────────────────────

    def scan_folders(self):
        src = self.source_folder.get().strip()
        if not src or not os.path.isdir(src):
            messagebox.showwarning("Invalid", "Please select a valid source folder.")
            return

        self.subfolders.clear()
        self.tree.delete(*self.tree.get_children())

        # Walk all nested subfolders
        for dirpath, dirnames, filenames in os.walk(src):
            # Skip the root folder itself
            if dirpath == src:
                # But check if root has images too (treat root as a subfolder)
                images = self._find_images(dirpath)
                if images:
                    rel = os.path.basename(src)
                    self.subfolders.append((dirpath, images, rel))
                    self.tree.insert("", tk.END, values=(
                        f"📁 {rel} (root)", len(images), "Ready"
                    ))
                continue

            images = self._find_images(dirpath)
            if images:
                rel = os.path.relpath(dirpath, src)
                # PDF name = subfolder name (last part of path)
                pdf_name = os.path.basename(dirpath)
                self.subfolders.append((dirpath, images, pdf_name))
                self.tree.insert("", tk.END, values=(
                    f"📁 {rel}", len(images), "Ready"
                ))

        total = len(self.subfolders)
        total_imgs = sum(len(imgs) for _, imgs, _ in self.subfolders)

        if total == 0:
            self.info_label.config(
                text="⚠️ No subfolders with images found!",
                fg="#f44336"
            )
        else:
            self.info_label.config(
                text=f"✅ Found {total} folder(s) with {total_imgs} total images. "
                     f"Double-click a row to preview. Press Ctrl+S to convert.",
                fg="#4CAF50"
            )

    def _find_images(self, folder):
        """Find all image files in a single folder, sorted naturally."""
        images = []
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in self.image_extensions:
                images.append(os.path.join(folder, f))
        images.sort(key=lambda p: natural_sort_key(os.path.basename(p)))
        return images

    # ── Preview ───────────────────────────────────────────────────────────────

    def preview_subfolder(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        idx = self.tree.index(selection[0])
        if idx >= len(self.subfolders):
            return

        dirpath, images, pdf_name = self.subfolders[idx]

        win = tk.Toplevel(self.root)
        win.title(f"Preview: {pdf_name}")
        win.geometry("450x400")
        win.configure(bg="#2b2b2b")
        win.grab_set()

        tk.Label(win, text=f"📁 {pdf_name}",
                 font=("Helvetica", 14, "bold"),
                 bg="#2b2b2b", fg="#ffffff").pack(pady=(12, 2))

        tk.Label(win, text=f"{len(images)} images — alphanumerically sorted",
                 font=("Helvetica", 10),
                 bg="#2b2b2b", fg="#aaaaaa").pack(pady=(0, 8))

        frame = tk.Frame(win, bg="#2b2b2b")
        frame.pack(fill="both", expand=True, padx=16, pady=4)

        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")

        lb = tk.Listbox(frame, font=("Consolas", 10),
                        bg="#1e1e1e", fg="#d4d4d4",
                        yscrollcommand=sb.set, relief="flat",
                        highlightthickness=1, highlightcolor="#007ACC",
                        activestyle="none")
        lb.pack(side="left", fill="both", expand=True)
        sb.config(command=lb.yview)

        for i, img_path in enumerate(images):
            lb.insert(tk.END, f"  {i+1:>3}.  {os.path.basename(img_path)}")

        tk.Button(win, text="Close", command=win.destroy,
                  font=("Helvetica", 11), bg="#555555", fg="white",
                  padx=20, pady=5, relief="flat", cursor="hand2"
                  ).pack(pady=10)

    # ── Conversion ────────────────────────────────────────────────────────────

    def start_conversion(self):
        if self.is_converting:
            return  # Already converting

        if not self.subfolders:
            messagebox.showwarning("Nothing to Convert",
                                   "Scan a source folder first.")
            return

        out = self.output_folder.get().strip()
        if not out:
            messagebox.showwarning("No Output", "Please select an output folder.")
            return

        # Create output folder if needed
        os.makedirs(out, exist_ok=True)

        # Disable button during conversion
        self.is_converting = True
        self.convert_btn.config(state="disabled", bg="#555555", text="⏳ Converting...")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.subfolders)

        # Run in thread so GUI doesn't freeze
        thread = threading.Thread(target=self._convert_all, args=(out,), daemon=True)
        thread.start()

    def _convert_all(self, output_dir):
        success = 0
        failed = 0
        skipped = 0

        for i, (dirpath, images, pdf_name) in enumerate(self.subfolders):
            row_id = self.tree.get_children()[i]

            # Update status
            self.root.after(0, lambda r=row_id: self.tree.set(r, "status", "⏳ Converting..."))
            self.root.after(0, lambda n=pdf_name: self.progress_label.config(
                text=f"Converting: {n}..."
            ))

            # Handle duplicate PDF names
            pdf_path = os.path.join(output_dir, f"{pdf_name}.pdf")
            counter = 1
            while os.path.exists(pdf_path):
                pdf_path = os.path.join(output_dir, f"{pdf_name} ({counter}).pdf")
                counter += 1

            try:
                image_list = []
                for img_path in images:
                    img = Image.open(img_path)
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    image_list.append(img)

                if not image_list:
                    self.root.after(0, lambda r=row_id: self.tree.set(
                        r, "status", "⚠️ No valid images"))
                    skipped += 1
                    continue

                first = image_list[0]
                rest = image_list[1:]

                first.save(
                    pdf_path, "PDF", resolution=100.0,
                    save_all=True, append_images=rest
                )

                final_name = os.path.basename(pdf_path)
                self.root.after(0, lambda r=row_id, n=final_name: self.tree.set(
                    r, "status", f"✅ {n}"))
                success += 1

            except Exception as e:
                self.root.after(0, lambda r=row_id, err=str(e): self.tree.set(
                    r, "status", f"❌ {err[:40]}"))
                failed += 1

            # Update progress
            self.root.after(0, lambda v=i+1: self._update_progress(v))

        # Done
        self.root.after(0, lambda: self._conversion_done(success, failed, skipped, output_dir))

    def _update_progress(self, value):
        self.progress["value"] = value

    def _conversion_done(self, success, failed, skipped, output_dir):
        self.is_converting = False
        self.convert_btn.config(state="normal", bg="#007ACC", text="🔄 Convert All to PDFs (Ctrl+S)")
        self.progress_label.config(text="Done!")

        msg = (
            f"Conversion complete!\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"⚠️ Skipped: {skipped}\n\n"
            f"📁 Output: {output_dir}"
        )

        if failed > 0:
            messagebox.showwarning("Done with Errors", msg)
        else:
            messagebox.showinfo("All Done!", msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = BatchFolderConverter(root)
    root.mainloop()
