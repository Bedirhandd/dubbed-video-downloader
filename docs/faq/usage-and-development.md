# Usage, Development, and Known Limitations

## Usage Patterns

### Can I download multiple videos at once?

Yes. Pass multiple URLs to the `download` command:

```bash
uv run dbdvdl download "URL1" "URL2" "URL3" --lang ja
```

All URLs share the same options (language, quality, etc.). If one fails, the others continue.

### Can I download a playlist?

Not yet. Playlist download is on the roadmap for a future release.

### Can I use this in a script?

Yes. Use `--default` to create config non-interactively, and `--yes` to auto-approve disk usage prompts:

```bash
#!/bin/bash
uv run dbdvdl init --default --default-lang ja --output-dir ~/Videos
uv run dbdvdl download "$URL" --yes --if-exists overwrite
```

### Can I use this with cron or systemd timers?

Yes, but be aware:

- Use `--yes` to auto-approve disk usage prompts
- Set `ask_for_disk_usage: false` in config or use `--yes`
- The `--if-exists` flag controls behavior for previously downloaded videos
- The `--dry-run` flag can be used to test without downloading

### How do I check if everything is set up correctly?

```bash
uv run dbdvdl doctor
```

This checks Python, config, FFmpeg, Node.js, and all Python packages.

## Development

### How do I run the tests?

```bash
uv sync --group dev
uv run pytest -v
```

Tests are fully offline by default. To allow network access during testing:

```bash
DBDVDL_TESTS_ALLOW_NETWORK=1 uv run pytest -v
```

### How do I run the linter?

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy
```

### What is the coverage threshold?

79%. The CI enforces `--fail-under=79` on coverage reports.

### How do I contribute?

See [CONTRIBUTING.md](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/CONTRIBUTING.md) for branch naming, commit conventions, and PR guidelines.

## Known Limitations

- **Linux only:** Windows and macOS are not supported
- **No playlist support:** Only individual video URLs are supported
- **No output format customization:** Video mode always outputs MKV, audio mode always outputs native format
- **No subtitle handling:** Only audio dubs are handled; subtitles are not downloaded or processed
- **No parallel downloads:** Multiple URLs are downloaded sequentially
- **YouTube only:** Only YouTube URLs are supported (via yt-dlp's YouTube extractor)

Features planned for future releases include batch downloading, output format customization, a GUI, and Windows compatibility.
