# YouTube Dubbed Video Downloader

A simple Python script that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) to download YouTube videos with a specific **dub language** (e.g., Turkish, English, Spanish).  

This tool is helpful if you want to:

- Download YouTube videos with **dubbed audio tracks** (multi-language support).  
- Save the output as `.mkv` files with both video and the chosen dubbed audio merged.  
- Organize downloaded videos by **language, channel, and title**.  
- Work with creators who provide **multiple audio tracks** on YouTube (e.g., MrBeast).  

It is basically a lightweight **YouTube multi-language video downloader** powered by yt-dlp.
The script saves videos in `.mkv` format and organizes them into this folder structure:

```

Videos/<lang>/<channel>/<title>/<title>.mkv

Example:

Videos/tr/MrBeast/World\_s\_Deadliest\_Obstacle\_Course/World\_s\_Deadliest\_Obstacle\_Course.mkv

```

## Tested Environment

- Python `3.11.4`
- `yt-dlp==2025.8.11`
- FFmpeg `N-117058-gceb471cfde-20240916`

---

## Requirements

- **Python** (>= 3.10 recommended)  
- **FFmpeg** (must be installed and accessible in your system PATH, or specify the full path in the script)

Check if you already have FFmpeg:

```bash
ffmpeg -version
```

If not installed, download it from the official site:
👉 [https://ffmpeg.org/](https://ffmpeg.org/)

---

## Installation

Clone the repo or copy the script file.

1. **Create a virtual environment** (recommended):

```bash
python -m venv env
```

Activate it:

* Windows:

  ```bash
  env\Scripts\activate
  ```
* Linux / macOS:

  ```bash
  source env/bin/activate
  ```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

`requirements.txt` should contain:

```
yt-dlp==2025.8.11
```

---

## Configuration

Open the script (`script.py`) and edit these lines if needed:

```python
DUB_LANGUAGE = "tr"   # Target dub language, e.g. "tr", "en"
FFMPEG_PATH = None    # Example: "C:/ffmpeg/ffmpeg.exe"
                      # Leave as None to let yt-dlp find FFmpeg in PATH
VIDEO_URLS = [
    "https://www.youtube.com/watch?v=EXAMPLE1",
    "https://www.youtube.com/watch?v=EXAMPLE2",
]
```

* `DUB_LANGUAGE`: set the language code you want (`"tr"`, `"en"`, etc.).
* `FFMPEG_PATH`: if FFmpeg is not in your system PATH, put its full path here.
* `VIDEO_URLS`: add the video URLs you want to download.

---

## Usage

Run the script:

```bash
python script.py
```

The script will:

1. Check if the requested dub language is available for each video.

   * If not, it will print an error with the list of available languages.
2. Download the video + the requested audio stream.
3. Merge them into `.mkv`.
4. Save them under `Videos/<lang>/<channel>/<title>/`.

---

## Notes

* If the script prints warnings like `WARNING: Unable to download format 616. Skipping...`, this is normal.
  yt-dlp tries multiple format IDs, and some may be unavailable. It automatically falls back to a working format.

* Output paths can be customized by editing the `outtmpl()` function in the script.

---

## Legal Disclaimer

* This script is provided for **educational and personal use only**.
* Respect YouTube’s [Terms of Service](https://www.youtube.com/static?template=terms) and the rights of content creators.
* Downloading and redistributing videos without permission may violate copyright laws.

---

```