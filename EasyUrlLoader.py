import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import yt_dlp


try:
    from aiohttp import web
    from server import PromptServer
except ImportError:  # pragma: no cover - allows importing the node outside ComfyUI
    web = None
    PromptServer = None


LOGGER = logging.getLogger("EasyUrlLoader")
DEFAULT_DOWNLOAD_ROOT = Path(__file__).resolve().parent / "downloads"
DEFAULT_SELECTION = {
    "version": 1,
    "full": {"enabled": True, "format": "bestvideo+bestaudio/best"},
    "audio": {"enabled": False, "format": "bestaudio"},
    "video": {"enabled": False, "format": "bestvideo"},
}
DEFAULT_SELECTION_JSON = json.dumps(DEFAULT_SELECTION, separators=(",", ":"))


def _normalise_url(url):
    value = str(url or "").strip()
    if not value:
        raise ValueError("Enter a URL before analyzing or downloading.")
    if "://" not in value:
        value = f"https://{value}"
    return value


def _number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _integer(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_size(value):
    size = _number(value, 0)
    if size <= 0:
        return ""
    units = ("B", "KB", "MB", "GB", "TB")
    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    precision = 0 if size >= 100 else 1
    return f"{size:.{precision}f} {units[index]}"


def _format_duration(value):
    seconds = _integer(value, 0)
    if seconds <= 0:
        return ""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _format_label(media_format, media_type):
    ext = str(media_format.get("ext") or "?").upper()
    width = _integer(media_format.get("width"), 0)
    height = _integer(media_format.get("height"), 0)
    fps = _number(media_format.get("fps"), 0)
    tbr = _number(media_format.get("tbr"), 0)
    abr = _number(media_format.get("abr"), 0)
    parts = []

    if media_type == "audio":
        if abr:
            parts.append(f"{round(abr)} kbps")
        sample_rate = _integer(media_format.get("asr"), 0)
        if sample_rate:
            parts.append(f"{round(sample_rate / 1000)} kHz")
        codec = str(media_format.get("acodec") or "").split(".")[0]
        if codec and codec != "none":
            parts.append(codec.upper())
        parts.append(ext)
        return " · ".join(parts)

    if width and height:
        parts.append(f"{width}×{height}")
    elif height:
        parts.append(f"{height}p")
    elif media_format.get("resolution"):
        parts.append(str(media_format["resolution"]))
    if fps:
        parts.append(f"{round(fps)} fps")
    if tbr:
        parts.append(f"{round(tbr)} kbps")
    codec = str(media_format.get("vcodec") or "").split(".")[0]
    if codec and codec != "none":
        parts.append(codec.upper())
    parts.append(ext)
    return " · ".join(parts) or "Available format"


def _format_entry(media_format, media_type, selector=None, suffix=""):
    format_id = str(media_format.get("format_id") or "").strip()
    size_bytes = _number(
        media_format.get("filesize") or media_format.get("filesize_approx"),
        0,
    )
    label = f"{_format_label(media_format, media_type)}{suffix}"
    if size_bytes and not suffix:
        label = f"{label} · {_format_size(size_bytes)}"
    return {
        "id": format_id,
        "format": selector or format_id,
        "label": label,
        "ext": str(media_format.get("ext") or ""),
        "width": _integer(media_format.get("width"), 0),
        "height": _integer(media_format.get("height"), 0),
        "fps": _number(media_format.get("fps"), 0),
        "tbr": _number(media_format.get("tbr"), 0),
        "abr": _number(media_format.get("abr"), 0),
        "size": _format_size(size_bytes),
        "size_bytes": size_bytes,
    }


def _sort_formats(formats, media_type):
    if media_type == "audio":
        return sorted(
            formats,
            key=lambda item: (item["abr"], item["size_bytes"], item["id"]),
            reverse=True,
        )
    return sorted(
        formats,
        key=lambda item: (item["height"], item["fps"], item["tbr"], item["width"], item["id"]),
        reverse=True,
    )


def _probe_url(url):
    """Extract format metadata without downloading media."""
    normalized_url = _normalise_url(url)
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(normalized_url, download=False)

    full_formats = []
    audio_formats = []
    video_formats = []
    seen_full = set()
    seen_audio = set()
    seen_video = set()

    for media_format in info.get("formats") or []:
        format_id = str(media_format.get("format_id") or "").strip()
        if not format_id:
            continue
        has_video = media_format.get("vcodec") not in (None, "none")
        has_audio = media_format.get("acodec") not in (None, "none")

        if has_video and has_audio and format_id not in seen_full:
            seen_full.add(format_id)
            full_formats.append(
                _format_entry(
                    media_format,
                    "video",
                    selector=format_id,
                    suffix=" · with audio",
                )
            )

        if has_video and not has_audio and format_id not in seen_video:
            seen_video.add(format_id)
            video_formats.append(_format_entry(media_format, "video"))

        if has_audio and not has_video and format_id not in seen_audio:
            seen_audio.add(format_id)
            audio_formats.append(_format_entry(media_format, "audio"))

    # The best video-only stream plus the best audio stream is usually the
    # highest-quality full-video choice on services such as YouTube.
    full_candidates = []
    full_candidate_selectors = set()
    for item in _sort_formats(video_formats, "video"):
        selector = f"{item['format']}+bestaudio/best"
        if selector in full_candidate_selectors:
            continue
        full_candidate_selectors.add(selector)
        full_candidates.append(
            {
                **item,
                "format": selector,
                "label": f"{item['label']} · + best audio",
            }
        )

    # Some services expose progressive video+audio streams instead of
    # separate streams. Include those choices as well.
    for item in _sort_formats(full_formats, "video"):
        if item["format"] in full_candidate_selectors:
            continue
        full_candidate_selectors.add(item["format"])
        full_candidates.append(item)

    full_candidates.sort(
        key=lambda item: (item["height"], item["fps"], item["tbr"], item["width"], item["id"]),
        reverse=True,
    )

    full_choices = [
        {
            "id": "auto",
            "format": "bestvideo+bestaudio/best",
            "label": "Best available · video + best audio",
            "ext": "mp4",
            "width": 0,
            "height": max((item["height"] for item in full_candidates), default=0),
            "fps": 0,
            "tbr": 0,
            "abr": 0,
            "size": "",
            "size_bytes": 0,
        }
    ]
    full_choices.extend(full_candidates[:39])

    # Keep the UI useful on sites that expose hundreds of duplicate formats.
    full_choices = full_choices[:40]
    audio_formats = _sort_formats(audio_formats, "audio")[:40]
    video_formats = _sort_formats(video_formats, "video")[:40]

    return {
        "url": normalized_url,
        "title": str(info.get("title") or "Untitled"),
        "uploader": str(info.get("uploader") or info.get("channel") or ""),
        "duration": _format_duration(info.get("duration")),
        "thumbnail": str(info.get("thumbnail") or ""),
        "formats": {
            "full": full_choices,
            "audio": audio_formats,
            "video": video_formats,
        },
    }


def _selection_from_value(value):
    if isinstance(value, dict):
        selection = value
    else:
        try:
            selection = json.loads(str(value or ""))
        except (TypeError, ValueError, json.JSONDecodeError):
            selection = {}

    if not isinstance(selection, dict):
        selection = {}

    parsed = {}
    defaults = {
        "full": (True, "bestvideo+bestaudio/best"),
        "audio": (False, "bestaudio"),
        "video": (False, "bestvideo"),
    }
    for name, (default_enabled, default_format) in defaults.items():
        value_for_output = selection.get(name)
        if not isinstance(value_for_output, dict):
            value_for_output = {}
        parsed[name] = {
            "enabled": bool(value_for_output.get("enabled", default_enabled)),
            "format": str(value_for_output.get("format") or default_format),
        }
    return parsed


def _output_directory(value, fallback):
    value = str(value or "").strip()
    path = Path(os.path.expandvars(os.path.expanduser(value))) if value else Path(fallback)
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _find_downloaded_file(directory, prepared_path, preferred_suffix=None):
    expected = Path(prepared_path)
    if preferred_suffix:
        preferred = expected.with_suffix(preferred_suffix)
        if preferred.is_file():
            return str(preferred)
    if expected.is_file():
        return str(expected)

    candidates = sorted(
        (path for path in directory.iterdir() if path.is_file() and path.stem == expected.stem),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return str(candidates[0]) if candidates else ""


def _download_one(url, directory, format_selector, media_type):
    options = {
        "format": format_selector,
        # Keep the name readable, but let yt-dlp remove characters that are
        # invalid or unreliable on Windows. The ID prevents collisions when
        # two videos have the same title and makes path recovery deterministic.
        "outtmpl": str(directory / "%(title).80s [%(id)s].%(ext)s"),
        "restrictfilenames": True,
        "windowsfilenames": True,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
    }
    if media_type == "full":
        options["merge_output_format"] = "mp4"
    elif media_type == "audio":
        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        ]

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        prepared_path = Path(ydl.prepare_filename(info))
        preferred_suffix = ".mp3" if media_type == "audio" else ".mp4" if media_type == "full" else None
        expected_path = prepared_path.with_suffix(preferred_suffix) if preferred_suffix else prepared_path

        if expected_path.is_file():
            LOGGER.info("%s already exists at %s", media_type.capitalize(), expected_path)
            return str(expected_path)

        ydl.download([url])

    result = _find_downloaded_file(directory, prepared_path, preferred_suffix)
    if not result:
        raise FileNotFoundError(f"Downloaded {media_type} file was not found in {directory}.")
    return result


def _choose_directory(initial_dir=""):
    initial_path = str(initial_dir or "").strip()
    if not os.path.isdir(initial_path):
        initial_path = str(Path.cwd())

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.update()
        try:
            selected = filedialog.askdirectory(
                parent=root,
                title="Choose an EasyUrl Loader output folder",
                initialdir=initial_path,
                mustexist=True,
            )
        finally:
            root.destroy()
        return os.path.abspath(selected) if selected else ""
    except Exception as tkinter_error:
        LOGGER.debug("tkinter folder picker unavailable: %s", tkinter_error)

    # Tk is not included in every Python distribution. Windows users still get
    # a native folder picker through PowerShell as a fallback.
    if sys.platform == "win32":
        script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
            f"$dialog.SelectedPath = '{initial_path.replace(chr(39), chr(39) + chr(39))}'; "
            "$dialog.Description = 'Choose an EasyUrl Loader output folder'; "
            "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
            "{ [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "[Console]::Write($dialog.SelectedPath) }"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return os.path.abspath(result.stdout.strip())

    raise RuntimeError("No native folder picker is available on the machine running ComfyUI.")


def _register_routes():
    if PromptServer is None or web is None:
        return
    prompt_server = getattr(PromptServer, "instance", None)
    if prompt_server is None or getattr(prompt_server, "_easyurl_loader_routes", False):
        return

    @prompt_server.routes.get("/easyurl/probe")
    async def easyurl_probe(request):
        url = request.rel_url.query.get("url", "")
        try:
            result = await asyncio.to_thread(_probe_url, url)
            return web.json_response(result)
        except Exception as error:
            LOGGER.exception("EasyUrl Loader could not analyze URL")
            return web.json_response({"error": str(error)}, status=400)

    @prompt_server.routes.get("/easyurl/select-directory")
    async def easyurl_select_directory(request):
        initial_dir = request.rel_url.query.get("initial", "")
        try:
            selected = await asyncio.to_thread(_choose_directory, initial_dir)
            return web.json_response({"path": selected})
        except Exception as error:
            LOGGER.exception("EasyUrl Loader could not open a folder picker")
            return web.json_response({"error": str(error)}, status=500)

    prompt_server._easyurl_loader_routes = True


class EasyUrlLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "https://www.youtube.com/watch?v=...",
                        "label": "Video URL",
                    },
                ),
                # These three values stay in the input order used by older
                # workflows. The custom JS panel hides them and mirrors its
                # output toggles into them for backwards compatibility.
                "download_full_video": ("BOOLEAN", {"default": True, "label": "Full video (managed by panel)"}),
                "download_audio": ("BOOLEAN", {"default": False, "label": "Audio (managed by panel)"}),
                "download_video": ("BOOLEAN", {"default": False, "label": "Video (managed by panel)"}),
                "full_output_dir": (
                    "STRING",
                    {"default": "", "label": "Full video output folder"},
                ),
                "audio_output_dir": (
                    "STRING",
                    {"default": "", "label": "Audio output folder"},
                ),
                "video_output_dir": (
                    "STRING",
                    {"default": "", "label": "Video-only output folder"},
                ),
                # This value is maintained by the custom JS panel. Keeping it
                # as a serialized widget makes selections travel with a saved
                # ComfyUI workflow and reach the execution backend.
                "download_selection": (
                    "STRING",
                    {"default": DEFAULT_SELECTION_JSON, "label": "Download selections"},
                ),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("full_video_path", "audio_path", "video_path")
    FUNCTION = "download_video"
    CATEGORY = "Custom Nodes"

    def download_video(
        self,
        url,
        download_full_video=True,
        download_audio=False,
        download_video=False,
        full_output_dir="",
        audio_output_dir="",
        video_output_dir="",
        download_selection=DEFAULT_SELECTION_JSON,
    ):
        full_video_path = ""
        audio_file_path = ""
        video_file_path = ""
        try:
            normalized_url = _normalise_url(url)
            selection = _selection_from_value(download_selection)
            default_selection = _selection_from_value(DEFAULT_SELECTION_JSON)
            if selection == default_selection and (
                bool(download_full_video) != default_selection["full"]["enabled"]
                or bool(download_audio) != default_selection["audio"]["enabled"]
                or bool(download_video) != default_selection["video"]["enabled"]
            ):
                selection = {
                    "full": {"enabled": bool(download_full_video), "format": "bestvideo+bestaudio/best"},
                    "audio": {"enabled": bool(download_audio), "format": "bestaudio"},
                    "video": {"enabled": bool(download_video), "format": "bestvideo"},
                }
            if not any(output["enabled"] for output in selection.values()):
                raise ValueError("Enable at least one download type in the EasyUrl Loader panel.")

            full_path = _output_directory(full_output_dir, DEFAULT_DOWNLOAD_ROOT / "full")
            audio_path = _output_directory(audio_output_dir, DEFAULT_DOWNLOAD_ROOT / "audio")
            video_path = _output_directory(video_output_dir, DEFAULT_DOWNLOAD_ROOT / "video")

            if selection["full"]["enabled"]:
                full_video_path = _download_one(
                    normalized_url,
                    full_path,
                    selection["full"]["format"],
                    "full",
                )

            if selection["audio"]["enabled"]:
                audio_file_path = _download_one(
                    normalized_url,
                    audio_path,
                    selection["audio"]["format"],
                    "audio",
                )

            if selection["video"]["enabled"]:
                video_file_path = _download_one(
                    normalized_url,
                    video_path,
                    selection["video"]["format"],
                    "video",
                )

            return (full_video_path, audio_file_path, video_file_path)
        except Exception as error:
            LOGGER.exception("Error processing EasyUrl Loader download")
            return (
                full_video_path or f"Error: {error}",
                audio_file_path,
                video_file_path,
            )


_register_routes()

NODE_CLASS_MAPPINGS = {"EasyUrlLoader": EasyUrlLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"EasyUrlLoader": "EasyUrl Loader"}
