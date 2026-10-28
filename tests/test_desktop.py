"""Offline tests for standalone downloader (no GUI/display/network required)."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from desktop import backend
from desktop.app import default_download_directory


class FakeYoutubeDL:
    instances = []

    def __init__(self, options):
        self.options = options
        self.info = {"id": "example123", "title": "Sample", "ext": "webm"}
        self.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def extract_info(self, url, download=False):
        self.url = url
        self.download_flag = download
        filename = Path(self.options["outtmpl"].replace("%(title).80s", "Sample").replace("%(id)s", "example123").replace("%(ext)s", "webm"))
        actual = filename.with_suffix(".mp3" if "postprocessors" in self.options else ".mp4" if "merge_output_format" in self.options else ".webm")
        actual.write_bytes(b"example")
        self.options["progress_hooks"][0]({"status": "downloading", "downloaded_bytes": 10, "total_bytes": 20})
        return self.info

    def prepare_filename(self, info):
        return self.options["outtmpl"].replace("%(title).80s", info["title"]).replace("%(id)s", info["id"]).replace("%(ext)s", info["ext"])


class DesktopBackendTests(unittest.TestCase):
    def test_default_directory_is_not_inside_app_bundle(self):
        self.assertEqual(default_download_directory(), Path.home() / "Downloads" / "EasyUrlLoader")

    def test_format_defaults(self):
        self.assertEqual(set(backend.DEFAULT_FORMATS), {"full", "audio", "video"})

    def test_bad_output_kind_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                backend.download("https://example.com/test", directory, "other")

    def test_analyze_uses_existing_comfyui_core(self):
        with patch.object(backend, "_probe_url", return_value={"title": "sample"}) as probe:
            self.assertEqual(backend.analyze("example.com"), {"title": "sample"})
            probe.assert_called_once_with("example.com")

    def test_full_audio_video_download_options_and_output(self):
        for kind, suffix in [("full", ".mp4"), ("audio", ".mp3"), ("video", ".webm")]:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                progress = []
                FakeYoutubeDL.instances.clear()
                with patch.object(backend, "bundled_ffmpeg", return_value="/some/ffmpeg"), patch.object(
                    backend.yt_dlp, "YoutubeDL", FakeYoutubeDL
                ):
                    result = backend.download(
                        "example.com/test", directory, kind, "customformat",
                        on_progress=lambda *_args: progress.append(_args),
                    )
                self.assertEqual(Path(result).suffix, suffix)
                self.assertTrue(Path(result).is_file())
                opts = FakeYoutubeDL.instances[-1].options
                self.assertEqual(opts["format"], "customformat")
                self.assertEqual(opts["ffmpeg_location"], "/some/ffmpeg")
                self.assertTrue(opts["noplaylist"])
                self.assertTrue(progress)
                self.assertEqual(FakeYoutubeDL.instances[-1].url, "https://example.com/test")
                self.assertTrue(FakeYoutubeDL.instances[-1].download_flag)

    def test_ffmpeg_exe_presence(self):
        with patch.object(backend.imageio_ffmpeg, "get_ffmpeg_exe", return_value="/missing/ffmpeg"), patch.object(backend.sys, "frozen", False, create=True):
            with self.assertRaises(RuntimeError):
                backend.bundled_ffmpeg()


if __name__ == "__main__":
    unittest.main()
