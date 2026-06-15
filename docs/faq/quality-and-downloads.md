# Quality and Downloads FAQ

## What video quality should I use?

| If you want... | Use... |
| --- | --- |
| The best available quality | `--video-quality best` |
| Good quality without huge file sizes | `--video-quality medium` (targets 720p) |
| Small file size | `--video-quality low` |
| A specific resolution | `--video-quality 1080p` (or any resolution from 144p to 8640p) |

## What audio quality should I use?

| If you want... | Use... |
| --- | --- |
| The best audio quality | `--audio-quality best` |
| A balance of quality and size | `--audio-quality medium` (targets ~128 kbps) |
| Smallest file size | `--audio-quality low` |

## Can I download audio only?

Yes. Use `--mode audio`:

```bash
uv run dbdvdl download "URL" --lang ja --mode audio --audio-quality best
```

This downloads only the dubbed audio stream in its native format (`.webm`, `.m4a`, etc.).

## Can I download video without audio?

No. The tool always downloads the audio track. The video mode downloads video + dubbed audio and merges them. There is no video-only mode.

## What format are downloaded videos?

Video-mode downloads are always `.mkv` (Matroska). Audio-mode downloads keep the native extension from YouTube.

## Can I customize the output format?

No. The output format is fixed: `.mkv` for video mode, native format for audio mode. Customization is on the roadmap for a future release.

## Where do downloaded files go?

Downloads follow this structure:

```
<output_dir>/<language>/<channel>/<title>/<title>.<ext>
```

For example, with the default output directory:

```
~/Downloads/dbdvdl-output/ja/SomeChannel/Video Title/Video Title.mkv
```
