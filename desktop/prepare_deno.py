"""Download and verify the official Deno runtime used by yt-dlp YouTube EJS."""

from pathlib import Path
import hashlib
import io
import platform
import re
import subprocess
import sys
from urllib.request import urlopen
import zipfile


TARGETS = {
    ("Windows", "AMD64"): "deno-x86_64-pc-windows-msvc.zip",
    ("Windows", "x86_64"): "deno-x86_64-pc-windows-msvc.zip",
    ("Darwin", "arm64"): "deno-aarch64-apple-darwin.zip",
    ("Darwin", "x86_64"): "deno-x86_64-apple-darwin.zip",
}


def fetch(url):
    with urlopen(url, timeout=120) as response:
        return response.read()


def main():
    key = (platform.system(), platform.machine())
    archive_name = TARGETS.get(key)
    if not archive_name:
        raise SystemExit(f"No Deno binary available for {key}")
    base = "https://github.com/denoland/deno/releases/latest/download/"
    archive = fetch(base + archive_name)
    sha_data = fetch(base + archive_name + ".sha256sum").decode("utf-8")
    digest_match = re.search(r"\b[a-fA-F0-9]{64}\b", sha_data)
    if not digest_match:
        raise SystemExit("Deno release has no SHA256 digest")
    expected = digest_match.group(0).lower()
    digest = hashlib.sha256(archive).hexdigest()
    if expected != digest:
        raise SystemExit(f"Deno checksum mismatch: {digest} != {expected}")
    binary_name = "deno.exe" if sys.platform == "win32" else "deno"
    destination = Path(__file__).resolve().parent / "vendor" / binary_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        with zipped.open(binary_name) as source, destination.open("wb") as output:
            while True:
                block = source.read(1024 * 1024)
                if not block:
                    break
                output.write(block)
    destination.chmod(destination.stat().st_mode | 0o111)
    completed = subprocess.run(
        [str(destination), "--version"], check=True, capture_output=True, text=True, timeout=30
    )
    if "deno" not in completed.stdout.lower():
        raise SystemExit("Downloaded runtime did not identify itself as Deno")
    print(f"Deno ready: {destination}; SHA256={digest}")


if __name__ == "__main__":
    main()
