import yt_dlp
from pathlib import Path

VIDEO_URLS = [
    # "https://www.youtube.com/watch?v=EXAMPLE1",
    # "https://www.youtube.com/watch?v=EXAMPLE2",
]

DUB_LANGUAGE = "tr"   # Target dub language, e.g., "tr", "en"
# Set your own FFmpeg path, or leave as None to let yt_dlp find it automatically
FFMPEG_PATH = None    # Example for Windows: "C:/ffmpeg/ffmpeg.exe"


def ydl_base_opts():
    """Options needed for YouTube multi-language audio extraction."""
    return {
        "extractor_args": {
            "youtube": {
                "player_client": ["all"],
            },
        },
        "js_runtimes": {
            "node": {},
        },
    }


def get_available_audio_langs(info):
    """Return the set of available audio languages for this video."""
    langs = set()
    for f in info.get("formats", []):
        if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none"):
            if f.get("language"):
                langs.add(f["language"])
    return langs

def ensure_lang(info, target):
    """Raise an error if the requested dub language is not available."""
    langs = get_available_audio_langs(info)
    if target not in langs:
        if not langs:
            raise RuntimeError(
                f"No multi-language audio tracks found for '{info.get('title')}'."
            )
        raise RuntimeError(
            f"Requested dub language not found for '{info.get('title')}'.\n"
            f"Requested: {target}\n"
            f"Available: {', '.join(sorted(langs))}"
        )

def outtmpl(lang):
    """Output template: Videos/<lang>/<uploader>/<title>/<title>.<ext>"""
    return f"Videos/{lang}/%(uploader)s/%(title)s/%(title)s.%(ext)s"

def download(url, lang, ffmpeg_path=None):
    """Download a single video with the specified dub language."""
    # First, fetch metadata to check available languages
    with yt_dlp.YoutubeDL({**ydl_base_opts(), "quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    ensure_lang(info, lang)

    ydl_opts = {
        **ydl_base_opts(),
        "format": f"bv*+bestaudio[language=\"{lang}\"]",
        "outtmpl": outtmpl(lang),
        "restrictfilenames": True,
        "merge_output_format": "mkv",
    }
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    Path(f"Videos/{DUB_LANGUAGE}").mkdir(parents=True, exist_ok=True)
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
