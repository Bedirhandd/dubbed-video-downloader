# Quality Selection

## Video Quality

Video quality can be specified at several levels of granularity:

**Presets:**

| Preset | Behavior |
| --- | --- |
| `best` | Highest available video resolution. |
| `medium` | Targets 720p. Picks the closest available height. |
| `low` | Lowest available video resolution. |

**Exact resolution:**

You can request a specific height like `1080p`, `720p`, `480p`. The value must be within `144p` through `8640p`. If the exact resolution is not available on the video, an error is raised listing all available options.

## Audio Quality

Audio quality always scoped to the selected dub language:

| Preset | Behavior |
| --- | --- |
| `best` | Highest available bitrate for the language. |
| `medium` | Targets approximately 128 kbps. Picks the audio stream closest to 128k. Falls back to `best` if bitrate metadata is unavailable from YouTube. |
| `low` | Lowest available bitrate for the language. Falls back to yt-dlp's `worstaudio` filter if bitrate metadata is unavailable. |

## Quality Inspection

The `qualities` command lets you preview what quality options exist before downloading:

```bash
dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr
```

This shows:
- All video resolution heights (e.g., `144p, 360p, 720p, 1080p`)
- All audio bitrate levels for the language (e.g., `128k, 256k`)
- Streams with unknown bitrate are flagged
