from pathlib import Path

from dubbed_video_downloader import core

VIDEO_URLS = [
    # "https://www.youtube.com/watch?v=EXAMPLE1",
    # "https://www.youtube.com/watch?v=EXAMPLE2",
]

DUB_LANGUAGE = "tr"   # Target dub language, e.g., "tr", "en"
# Set your own FFmpeg path, or leave as None to let yt_dlp find it automatically
FFMPEG_PATH = None    # Example for Windows: "C:/ffmpeg/ffmpeg.exe"


def main():
    Path(f"Videos/{DUB_LANGUAGE}").mkdir(parents=True, exist_ok=True)
    if not VIDEO_URLS:
        print("Please add YouTube video links to download.")
        return
    for u in VIDEO_URLS:
        try:
            print(f"\n==> Downloading: {u}")
            core.download(u, DUB_LANGUAGE, FFMPEG_PATH)
            print("Finished")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
