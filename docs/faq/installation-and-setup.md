# Installation and Setup FAQ

## Why do I need Node.js?

YouTube serves some video data via JavaScript that must be executed to extract stream URLs. The `yt-dlp-ejs` package uses Node.js as a JavaScript runtime for this purpose. Without Node.js, yt-dlp cannot extract some YouTube video formats.

## I get "Config file not found" errors. What do I do?

Run `uv run dbdvdl init` to create the configuration file. This is required before using any other command.

## How do I reset my config?

```bash
uv run dbdvdl config remove      # removes the config directory
uv run dbdvdl init               # create a fresh config
```

## Can I use a config file from a different location?

No. The config is always read from `~/.config/dubbed-video-downloader/config.yaml`. There is no `--config` flag to specify an alternative path.

## Why does `doctor` warn about config permissions?

On POSIX systems, `dbdvdl init` creates the config directory as `0700` and `config.yaml` as `0600`. If an older or manually edited config is world-readable, `doctor` reports a `Config permissions` warning with recommended `chmod` commands. The check still reports `OK` and does not block downloads. See [Configuration Overview](../configuration/overview.md#file-permissions) and [doctor](../commands/doctor.md).
