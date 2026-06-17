# `dbdvdl qualities`

**Description:** Show available video quality options and dubbed audio quality options for a given URL and language.

**Usage:**

```
dbdvdl qualities [OPTIONS] URL
```

## Arguments

| Name | Required | Description |
| --- | --- | --- |
| `URL` | Yes | YouTube video URL to inspect. Must use `http` or `https` and include a host. |

## Options

### `--lang`, `-l`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Config default (`default_lang`) |
| Description | Target dub language code. Overrides the config default. Must be a valid BCP-47 language code. |

### `--verbose`, `-v`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Show yt-dlp progress, info, and warnings during metadata extraction. |

### `--debug`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Show yt-dlp debug output and Python error tracebacks on failure. |

### `--retry-on-network-failure`

| Property | Value |
| --- | --- |
| Type | `int` |
| Default | Value from config (default: `3`) |
| Description | Network retries for metadata and extraction. Overrides the config value. Must be a non-negative integer. |

## Examples

```bash
dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID"
dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja
dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr --verbose
```

## Output

Shows:

- **Title** -- video title
- **Channel** -- uploader name
- **Language** -- resolved language tag (with track tag if different from canonical)
- **Available languages** -- all languages on the video
- **Video qualities** -- available video heights (e.g., `144p, 360p, 720p, 1080p`) or `none found`
- **Audio qualities** -- available audio bitrates for the selected language (e.g., `128k, 256k`) or `unknown bitrate` if bitrate metadata is unavailable
