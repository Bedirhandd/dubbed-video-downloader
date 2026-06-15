# Download Modes

## Video Mode (`--mode video`)

Downloads both the best video stream (no audio) and the selected dubbed audio stream, then merges them using FFmpeg into an MKV container.

- Output format: `.mkv` (Matroska)
- The video stream selected uses `vcodec!=none,acodec=none` filter
- The audio stream selected uses `vcodec=none,acodec!=none,language="<lang>"` filter

## Audio Mode (`--mode audio`)

Downloads only the selected dubbed audio stream. No video is downloaded.

- Output format: native (`.webm`, `.m4a`, etc. -- whatever YouTube provides)
- Useful for extracting dubbed audio tracks without the video
