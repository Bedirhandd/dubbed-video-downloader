import yt_dlp
import os
from pathlib import Path

VIDEO_URLS = [
    # "https://www.youtube.com/watch?v=EXAMPLE1",
    # "https://www.youtube.com/watch?v=EXAMPLE2",
]

DUB_LANGUAGE = "en-US"   # Target dub language, e.g., "tr", "en"
# Set your own FFmpeg path, or leave as None to let yt_dlp find it automatically
FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe"    # Example for Windows: "C:/ffmpeg/ffmpeg.exe"

def get_downloads_dir():
    """
    Cross-platform Downloads directory resolution.
    - Linux: uses XDG user-dirs if available
    - Windows: uses ~/Downloads
    - Fallback: ~/Downloads
    """
    # Linux (XDG)
    xdg_dir = os.environ.get("XDG_DOWNLOAD_DIR")
    if xdg_dir:
        # Strip surrounding quotes if present
        return Path(xdg_dir.strip('"')).expanduser()

    # Default fallback (Windows & Linux)
    return Path.home() / "Downloads"

# Resolve Windows Downloads folder
DOWNLOADS_DIR = get_downloads_dir()

def get_available_audio_langs(info):
    """Return sorted list of available audio languages."""
    langs = set()
    for f in info.get("formats", []):
        if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none"):
            if f.get("language"):
                langs.add(f["language"])
    return sorted(langs)

def resolve_language(info, requested):
    """
    Resolve requested language to best available match.
    Priority:
      1. Exact match (en-US)
      2. Prefix match (en -> en-US, en-GB)
    """
    available = get_available_audio_langs(info)

    if not available:
        raise RuntimeError(
            f"No multi-language audio tracks found for '{info.get('title')}'."
        )

    # Exact match
    if requested in available:
        return requested

    # Partial prefix match (e.g. "en" -> "en-US")
    prefix_matches = [
        lang for lang in available
        if lang.lower().startswith(requested.lower() + "-")
    ]

    if prefix_matches:
        return sorted(prefix_matches)[0]

    raise RuntimeError(
        f"Requested language '{requested}' not found.\n"
        f"Available: {', '.join(available)}"
    )

def outtmpl(lang):
    base = DOWNLOADS_DIR / "YouTube" / lang
    return str(base / "%(uploader)s/%(title)s/%(title)s.%(ext)s")

def download(url, lang, ffmpeg_path=None):
    """Download a single video with the specified dub language."""
    # First, fetch metadata to check available languages
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    resolved_lang = resolve_language(info, lang)
    print(f"→ Using audio language: {resolved_lang}")

    ydl_opts = {
        "format": f"bv*+bestaudio[language=\"{resolved_lang}\"]",
        "outtmpl": outtmpl(lang),
        "restrictfilenames": True,
        "merge_output_format": "mkv",
    }
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    if not VIDEO_URLS:
        print("Please add YouTube video links to download.")
        return
    for u in VIDEO_URLS:
        try:
            print(f"\n==> Downloading: {u}")
            download(u, DUB_LANGUAGE, FFMPEG_PATH)
            print("✔ Finished")
        except Exception as e:
            print(f"✖ Error: {e}")

if __name__ == "__main__":
    main()
