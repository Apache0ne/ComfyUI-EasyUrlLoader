"""Reuse the ComfyUI node's URL probing logic with desktop download/progress support."""

from pathlib import Path
import os
import shutil
import subprocess
import sys

import imageio_ffmpeg
import yt_dlp

from EasyUrlLoader import _find_downloaded_file, _normalise_url, _probe_url


DEFAULT_FORMATS = {
    "full": "bestvideo+bestaudio/best",
    "audio": "bestaudio",
    "video": "bestvideo",
}


def bundled_ffmpeg():
    """Provide yt-dlp a binary with the canonical ffmpeg(.exe) filename."""
    binary_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    if getattr(sys, "frozen", False):
        binary = Path(sys._MEIPASS) / binary_name
        if not binary.is_file():
            raise RuntimeError("The bundled FFmpeg binary is missing from this app build")
        return str(binary)

    # The imageio wheel names its binary ffmpeg-<platform>-<version>.
    # yt-dlp expects ffmpeg or ffmpeg.exe as ffmpeg_location.
    upstream = Path(imageio_ffmpeg.get_ffmpeg_exe())
    if not upstream.is_file():
        raise RuntimeError("FFmpeg was not found. Install imageio-ffmpeg")
    if upstream.name == binary_name:
        return str(upstream)
    cache = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / ".cache")) / "EasyUrlLoader" / "tools"
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / binary_name
    if not target.is_file() or target.stat().st_size != upstream.stat().st_size:
        temp = cache / (binary_name + ".tmp")
        shutil.copy2(upstream, temp)
        temp.chmod(temp.stat().st_mode | 0o111)
        temp.replace(target)
    return str(target)


def bundled_deno():
    """Return bundled Deno in frozen apps, or an installed Deno for source runs."""
    name = "deno.exe" if sys.platform == "win32" else "deno"
    if getattr(sys, "frozen", False):
        binary = Path(sys._MEIPASS) / name
        if not binary.is_file():
            raise RuntimeError("The bundled Deno runtime is missing from this app build")
        return str(binary)
    return shutil.which("deno")


def configure_js_runtime():
    """Make Deno visible to the existing ComfyUI probe and to yt-dlp."""
    deno = bundled_deno()
    if deno:
        directory = str(Path(deno).parent)
        current = os.environ.get("PATH", "")
        if directory not in current.split(os.pathsep):
            os.environ["PATH"] = directory + os.pathsep + current
    return deno


def self_test():
    """Smoke-test prerequisites without launching a window or using the network."""
    binary = bundled_ffmpeg()
    completed = subprocess.run(
        [binary, "-version"], capture_output=True, text=True, timeout=20, check=True
    )
    if not completed.stdout.startswith("ffmpeg version"):
        raise RuntimeError("FFmpeg reported an unexpected version response")
    assert _normalise_url("example.com") == "https://example.com"
    deno = configure_js_runtime()
    if deno:
        result = subprocess.run([deno, "--version"], capture_output=True, text=True, timeout=20, check=True)
        if "deno" not in result.stdout.lower():
            raise RuntimeError("Deno runtime self-test failed")
    print("EasyUrlLoader desktop self-test OK: FFmpeg, yt-dlp, URL core")


def analyze(url):
    configure_js_runtime()
    return _probe_url(url)


def download(url, directory, kind, selector=None, on_progress=None):
    """Download one selected output. Run from a worker thread, not the UI thread."""
    if kind not in DEFAULT_FORMATS:
        raise ValueError(f"Unsupported output type: {kind}")

    url = _normalise_url(url)
    output = (Path(directory).expanduser() / kind).resolve()
    output.mkdir(parents=True, exist_ok=True)
    selector = selector or DEFAULT_FORMATS[kind]
    ffmpeg_path = bundled_ffmpeg()
    deno = configure_js_runtime()

    def progress_hook(event):
        if not on_progress:
            return
        if event.get("status") == "downloading":
            total = event.get("total_bytes") or event.get("total_bytes_estimate")
            done = event.get("downloaded_bytes", 0)
            percent = min(100, round(100 * done / total)) if total else None
            on_progress(kind, percent, event.get("_speed_str", ""))
        elif event.get("status") == "finished":
            on_progress(kind, 100, "Processing…")

    options = {
        "format": selector,
        "outtmpl": str(output / "%(title).80s [%(id)s].%(ext)s"),
        "noplaylist": True,
        "restrictfilenames": True,
        "windowsfilenames": True,
        "ffmpeg_location": ffmpeg_path,
        "quiet": True,
        "no_warnings": False,
        "overwrites": False,
        "progress_hooks": [progress_hook],
    }
    if deno:
        options["js_runtimes"] = {"deno": {"path": deno}}
    if kind == "full":
        options["merge_output_format"] = "mp4"
    elif kind == "audio":
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0",
        }]

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise RuntimeError("The site did not return download information")
        predicted = ydl.prepare_filename(info)

    suffix = ".mp3" if kind == "audio" else ".mp4" if kind == "full" else None
    path = _find_downloaded_file(output, predicted, suffix)
    if not path:
        raise FileNotFoundError("The download finished, but the output file could not be located")
    return path
