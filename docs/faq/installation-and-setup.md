# Installation and Setup FAQ

## How do I install dbdvdl?

**Recommended** — isolated CLI environment with [pipx](https://pipx.pypa.io/):

```bash
pipx install dubbed-video-downloader
```

**Alternative** — install with pip into a virtual environment or with `--user`:

```bash
pip install dubbed-video-downloader
```

See [Installation](../getting-started/installation.md) for prerequisites (FFmpeg, Node.js) and [Quickstart](../getting-started/quickstart.md) for config setup.

## pipx vs pip — which should I use?

**pipx** keeps `dbdvdl` and its Python dependencies in a dedicated environment and exposes only the `dbdvdl` command on your `PATH`. This is the recommended option for a standalone CLI.

**pip** installs into the active Python environment (venv, `--user`, or system). Use this if you already manage Python packages in a venv or prefer not to install pipx.

## I get "command not found: dbdvdl". What do I do?

- **pipx:** Ensure pipx's bin directory is on your `PATH`. Run `pipx ensurepath`, then open a new shell.
- **pip:** Activate the virtual environment you installed into, or ensure `~/.local/bin` is on your `PATH` when using `pip install --user`.

Verify with `dbdvdl --version`.

## Why do I need Node.js?

YouTube serves some video data via JavaScript that must be executed to extract stream URLs. The `yt-dlp-ejs` package uses Node.js as a JavaScript runtime for this purpose. Without Node.js, yt-dlp cannot extract some YouTube video formats.

## I get "Config file not found" errors. What do I do?

Run `dbdvdl init` to create the configuration file. This is required before using any other command.

## How do I reset my config?

```bash
dbdvdl config remove      # removes the config directory
dbdvdl init               # create a fresh config
```

## Can I use a config file from a different location?

No. The config is always read from `~/.config/dubbed-video-downloader/config.yaml`. There is no `--config` flag to specify an alternative path.

## Why does `doctor` warn about config permissions?

On POSIX systems, `dbdvdl init` creates the config directory as `0700` and `config.yaml` as `0600`. If an older or manually edited config is world-readable, `doctor` reports a `Config permissions` warning with recommended `chmod` commands. The check still reports `OK` and does not block downloads. See [Configuration Overview](../configuration/overview.md#file-permissions) and [doctor](../commands/doctor.md).
