# `dbdvdl langs`

**Description:** List the dubbed audio language codes available for a given YouTube video URL.

**Usage:**

```
dbdvdl langs [OPTIONS] URL
```

## Arguments

| Name | Required | Description |
| --- | --- | --- |
| `URL` | Yes | YouTube video URL to inspect. Must use `http` or `https` and include a host. |

## Options

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
dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"
dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID" --retry-on-network-failure 5
dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

## Output

Prints one language tag per line in sorted, standardized BCP-47 format. Exits with code `1` if no valid audio languages are found.

```
en
es
fr
ja
```

If some audio tracks have invalid or undefined language metadata, a warning is printed to stderr but valid languages are still listed.
