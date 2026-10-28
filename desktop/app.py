"""Native, zero-ComfyUI desktop interface for the Universal URL Downloader."""

import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from desktop import backend


LABELS = {
    "full": "Full video + audio (MP4)",
    "audio": "Audio only (MP3)",
    "video": "Video only",
}


def default_download_directory():
    return Path.home() / "Downloads" / "EasyUrlLoader"


def open_directory(directory):
    path = Path(directory).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class DownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EasyUrlLoader · Universal URL Downloader")
        self.geometry("760x590")
        self.minsize(610, 490)

        self.events = queue.Queue()
        self.busy = False
        self.url = tk.StringVar()
        self.directory = tk.StringVar(value=str(default_download_directory()))
        self.status = tk.StringVar(value="Enter a media URL and click Analyze URL.")
        self.title_var = tk.StringVar(value="")
        self.progress = tk.DoubleVar(value=0)
        self.selected = {kind: tk.BooleanVar(value=kind == "full") for kind in LABELS}
        self.quality = {kind: tk.StringVar(value="Best available") for kind in LABELS}
        self.available = {kind: [("Best available", backend.DEFAULT_FORMATS[kind])] for kind in LABELS}

        self._build_ui()
        self.after(100, self._poll_events)

    def _build_ui(self):
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        ttk.Label(outer, text="Universal URL Downloader", font=("TkDefaultFont", 18, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )
        ttk.Label(outer, text="Video or audio URL").grid(row=1, column=0, sticky="w")
        url_row = ttk.Frame(outer)
        url_row.grid(row=2, column=0, sticky="ew", pady=(5, 12))
        url_row.columnconfigure(0, weight=1)
        entry = ttk.Entry(url_row, textvariable=self.url)
        self.url_entry = entry
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        entry.bind("<Return>", lambda _event: self.analyze())
        self.analyze_button = ttk.Button(url_row, text="Analyze URL", command=self.analyze)
        self.analyze_button.grid(row=0, column=1)

        ttk.Label(outer, textvariable=self.title_var, wraplength=690).grid(
            row=3, column=0, sticky="w", pady=(0, 8)
        )

        choices = ttk.LabelFrame(outer, text="Select outputs and quality", padding=12)
        choices.grid(row=4, column=0, sticky="ew", pady=(2, 16))
        choices.columnconfigure(1, weight=1)
        self.quality_boxes = {}
        for row, (kind, label) in enumerate(LABELS.items()):
            ttk.Checkbutton(choices, text=label, variable=self.selected[kind]).grid(
                row=row, column=0, sticky="w", padx=(0, 16), pady=6
            )
            widget = ttk.Combobox(
                choices, textvariable=self.quality[kind], state="readonly", width=47,
                values=["Best available"],
            )
            widget.grid(row=row, column=1, sticky="ew", pady=6)
            self.quality_boxes[kind] = widget

        ttk.Label(outer, text="Save downloads in").grid(row=5, column=0, sticky="w")
        folder_row = ttk.Frame(outer)
        folder_row.grid(row=6, column=0, sticky="ew", pady=(5, 12))
        folder_row.columnconfigure(0, weight=1)
        ttk.Entry(folder_row, textvariable=self.directory).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.browse_button = ttk.Button(folder_row, text="Browse…", command=self.browse)
        self.browse_button.grid(row=0, column=1, padx=(0, 8))
        ttk.Button(folder_row, text="Open folder", command=self.open_folder).grid(row=0, column=2)

        self.download_button = ttk.Button(
            outer, text="Download selected", command=self.start_download
        )
        self.download_button.grid(row=7, column=0, sticky="ew", pady=(0, 10))
        ttk.Progressbar(outer, variable=self.progress, maximum=100).grid(
            row=8, column=0, sticky="ew", pady=(0, 9)
        )
        ttk.Label(outer, textvariable=self.status, wraplength=690).grid(
            row=9, column=0, sticky="w", pady=(0, 8)
        )

        outer.rowconfigure(10, weight=1)
        log_frame = ttk.Frame(outer)
        log_frame.grid(row=10, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=5, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=scrollbar.set)
        self._log("Ready. Files are saved in separate full/audio/video subfolders.")
        entry.focus_set()

    def _log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", f"{message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.analyze_button.configure(state=state)
        self.download_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.url_entry.configure(state=state)

    def browse(self):
        folder = filedialog.askdirectory(initialdir=self.directory.get(), mustexist=True)
        if folder:
            self.directory.set(folder)

    def open_folder(self):
        try:
            open_directory(self.directory.get())
        except Exception as exc:
            messagebox.showerror("Cannot open folder", str(exc), parent=self)

    def _start_worker(self, target):
        self._set_busy(True)
        self.progress.set(0)
        threading.Thread(target=target, daemon=True).start()

    def analyze(self):
        url = self.url.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Enter a URL to analyze.", parent=self)
            return
        if self.busy:
            return
        self.title_var.set("")
        self.status.set("Analyzing available formats…")

        def worker():
            try:
                info = backend.analyze(url)
                self.events.put(("analyzed", info))
            except Exception as exc:
                self.events.put(("error", str(exc)))

        self._start_worker(worker)

    def _populate_formats(self, info):
        self.title_var.set(f"{info.get('title', 'Untitled')}  ·  {info.get('duration', '')}")
        for kind in LABELS:
            options = [("Best available", backend.DEFAULT_FORMATS[kind])]
            formats = info.get("formats", {}).get(kind) or []
            already = {backend.DEFAULT_FORMATS[kind]}
            for item in formats:
                selector = str(item.get("format") or "")
                if not selector or selector in already:
                    continue
                already.add(selector)
                label = f"{item.get('label', selector)}  [{len(options)}]"
                options.append((label, selector))
            self.available[kind] = options
            self.quality_boxes[kind].configure(values=[item[0] for item in options])
            self.quality[kind].set(options[0][0])

    def start_download(self):
        if self.busy:
            return
        url = self.url.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Enter a media URL.", parent=self)
            return
        kinds = [kind for kind in LABELS if self.selected[kind].get()]
        if not kinds:
            messagebox.showwarning("No outputs", "Select at least one download type.", parent=self)
            return
        target = self.directory.get().strip()
        if not target:
            messagebox.showwarning("Missing folder", "Choose a download folder.", parent=self)
            return
        selections = []
        for kind in kinds:
            label = self.quality[kind].get()
            selector = next(
                (value for name, value in self.available[kind] if name == label),
                backend.DEFAULT_FORMATS[kind],
            )
            selections.append((kind, selector))
        self.status.set("Downloading…")

        def worker():
            try:
                for index, (kind, selector) in enumerate(selections):
                    self.events.put(("status", f"Downloading {LABELS[kind]} ({index+1}/{len(selections)})…"))

                    def progress(_kind, percent, speed):
                        if percent is not None:
                            self.events.put(("progress", (index * 100 + percent) / len(selections)))
                        if speed == "Processing…":
                            self.events.put(("status", f"Processing {LABELS[kind]}…"))

                    result = backend.download(url, target, kind, selector, on_progress=progress)
                    self.events.put(("log", f"Saved {kind}: {result}"))
                    self.events.put(("progress", (index + 1) * 100 / len(selections)))
                self.events.put(("done", "Downloads complete."))
            except Exception as exc:
                self.events.put(("error", str(exc)))

        self._start_worker(worker)

    def _poll_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "analyzed":
                    self._populate_formats(value)
                    self.status.set("Formats found. Choose outputs and download.")
                    self._log(f"Analyzed: {value.get('title', 'Untitled')}")
                    self._set_busy(False)
                elif kind == "progress":
                    self.progress.set(value)
                elif kind == "status":
                    self.status.set(value)
                elif kind == "log":
                    self._log(value)
                elif kind == "done":
                    self.progress.set(100)
                    self.status.set(value)
                    self._log(value)
                    self._set_busy(False)
                elif kind == "error":
                    self.status.set(f"Error: {value}")
                    self._log(f"ERROR: {value}")
                    self._set_busy(False)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)


def main():
    if "--self-test" in sys.argv:
        backend.self_test()
        return
    app = DownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
