# Universal URL Downloader — standalone desktop app

This branch includes a separate desktop UI for the existing downloader. The desktop app **does not require ComfyUI, Python, or a separately installed FFmpeg**. It uses the branch's `EasyUrlLoader.py` URL probing/format choices, bundles `yt-dlp`, its EJS YouTube challenge scripts, verified native Deno runtime, and an FFmpeg executable via `imageio-ffmpeg`, and saves full videos, audio-only MP3, or video-only tracks into separate subfolders.

## Download

[Releases](https://github.com/Apache0ne/ComfyUI-EasyUrlLoader/releases) provides tested, branch-specific **prerelease** assets after the GitHub Action completes:

- **Windows x64**: `EasyUrlLoader-Windows-x64.exe` — download, then double-click. No installer or Python setup.
- **macOS Apple Silicon (M1/M2/M3/M4/...)**: `EasyUrlLoader-macOS-Apple-Silicon.zip` — unzip, then open `EasyUrlLoader.app`.
- **macOS Intel**: `EasyUrlLoader-macOS-Intel.zip` — unzip, then open `EasyUrlLoader.app`.

Unsigned Windows executables may raise a SmartScreen warning. These macOS builds are currently **not Apple Developer ID signed or notarized** and macOS Gatekeeper may block a normal double-click: use Finder → Control-click `EasyUrlLoader.app` → Open, and follow macOS's prompts (System Settings → Privacy & Security → Open Anyway if offered). The project would need Developer ID signing and Apple notarization to launch without that warning on all Macs. Only run software you trust.

GitHub Actions also retains the three build artifacts under the corresponding run for 30 days. A workflow run publishes a prerelease only **after all three platform builds and smoke tests succeed**.

## Use

1. Paste a video/media URL, click **Analyze URL** to see available quality choices (or skip analysis for automatic best quality).
2. Check one or more of **Full video + audio**, **Audio only**, or **Video only**, choose the quality for each, and select an output folder.
3. Click **Download selected**. The progress bar and log display progress and saved file locations. **Open folder** opens the destination.

Some sites restrict media extraction, require accounts/cookies, or change formats; `yt-dlp` cannot download everything. Only download content you are authorized to access.

## Build / test locally

Use Python 3.12 with Tk available. For full YouTube support in source mode, install Deno 2.3+ on your PATH; the downloadable builds already include Deno:

```bash
python -m pip install -r desktop/requirements-build.txt
python -m unittest discover -s tests -v
python -m desktop
python -m desktop --self-test
```

The workflow `.github/workflows/build-desktop.yml` targets only the `Universal-URLdownloader` branch (`push` plus manual dispatch), using Windows x64, macOS ARM64 and macOS Intel runners. PyInstaller produces a one-file Windows `.exe` and native macOS `.app` bundles zipped with `ditto`; all use bundled FFmpeg, Deno, and yt-dlp EJS scripts. After a successful build, it creates a uniquely tagged **prerelease pointing to the tested branch SHA**, without touching `main`.

Note: FFmpeg binaries distributed by `imageio-ffmpeg` have their own codec and LGPL/GPL licensing considerations. Review the shipped FFmpeg build's `-L` and `-version` outputs before public redistribution, and satisfy all applicable notice/source obligations.
