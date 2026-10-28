"""Stage the exact FFmpeg wheel executable for PyInstaller using its standard name."""

from pathlib import Path
import shutil
import subprocess
import sys

import imageio_ffmpeg


def main():
    source = Path(imageio_ffmpeg.get_ffmpeg_exe())
    if not source.is_file():
        raise SystemExit("imageio-ffmpeg wheel has no FFmpeg binary")
    target = Path(__file__).resolve().parent / "vendor" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | 0o111)
    subprocess.run([str(target), "-version"], check=True, capture_output=True, timeout=20)
    print(f"FFmpeg staged: {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
