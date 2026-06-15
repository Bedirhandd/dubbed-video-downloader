# Config Management

## Show Config

```bash
uv run dbdvdl config show
```

Prints all resolved config values. Useful to verify what the app is using.

## Remove Config

```bash
uv run dbdvdl config remove
uv run dbdvdl config remove --yes
```

Removes the entire config directory (`~/.config/dubbed-video-downloader/`). After removal, most commands will fail until a new config is created with `dbdvdl init`.

## Recreate Config

To recreate the config after removal or to start fresh:

```bash
uv run dbdvdl init
uv run dbdvdl init --default
```

## Config Validation

When loading the config, the following checks are performed:

- **Missing required keys** -- `output_dir`, `ffmpeg_path`, and `default_lang` must be present. Missing any of these produces a `ConfigError`.
- **Type validation** -- each key's value is validated for correct type (strings for paths and language, enums for modes and behaviors, integers for retries, boolean for disk usage).
- **Path validation** -- `output_dir` must resolve to an absolute path. `ffmpeg_path` must be either `ffmpeg`/`ffmpeg.exe` or an absolute path.
- **Language validation** -- `default_lang` is checked to be a non-empty string at load time. Full BCP-47 validation (including rejection of `und`) occurs when the config is written (via `dbdvdl init`) and when the language code is used by other commands at runtime.
- **Quality validation** -- video and audio quality values must be valid presets or resolutions within the allowed ranges (144p-8640p for video).
- **Behavior validation** -- download mode, exists behavior, and other enum values must be one of the accepted variants.
