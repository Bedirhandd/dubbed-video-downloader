# Configuration Overview

Dubbed Video Downloader stores its configuration in a YAML file at `~/.config/dubbed-video-downloader/config.yaml`. This file is created by `dbdvdl init` and read by all other commands.

## Config File Location

| OS | Path |
| --- | --- |
| Linux | `~/.config/dubbed-video-downloader/config.yaml` |

The config directory is determined by `Path.home() / ".config" / "dubbed-video-downloader"` at runtime.

## Config File Format

The config file is a YAML mapping with the following keys:

```yaml
output_dir: ~/Downloads/dbdvdl-output
ffmpeg_path: ffmpeg
default_lang: en
default_download_mode: video
default_video_quality: best
default_audio_quality: best
retry_on_network_failure: 3
default_exists_behavior: skip
ask_for_disk_usage: false
```

All keys are written in the order shown above. Unknown keys in the file are silently ignored, allowing forward compatibility.

## CLI Override Behavior

All config keys can be overridden at the command line via the corresponding CLI option on individual commands. The override precedence is:

1. **CLI flag** (highest priority) -- specified directly on the command line
2. **Config file** -- loaded from `~/.config/dubbed-video-downloader/config.yaml`
3. **Built-in default** (lowest priority) -- only used when the key is optional and absent from config

For example, `--lang ja` on the `download` command overrides `default_lang` from the config file for that single run only. The config file is never modified by a CLI override.

## Environment Variables

The project does not use environment variables for operational configuration. The only environment variable is test-only:

| Variable | Purpose |
| --- | --- |
| `DBDVDL_TESTS_ALLOW_NETWORK` | Set to `1` to allow network access during test runs. By default, tests are fully offline. |
