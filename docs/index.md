# Dubbed Video Downloader -- Documentation

**Version:** 0.2.0

Dubbed Video Downloader (`dbdvdl`) is a Python CLI tool that wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) to download YouTube videos or audio tracks with a selected dubbed audio language. It is designed for a language-first workflow: list available dubs, pick a language and quality, then download with organized output.

## Documentation Index

### Getting Started

| Document | Description |
| --- | --- |
| [Installation](getting-started/installation.md) | PyPI install (pipx/pip), install from source, and dev tools |
| [Dependencies](getting-started/dependencies.md) | Complete dependency reference -- runtime, system, and development packages |
| [Quickstart](getting-started/quickstart.md) | Config setup, doctor verification, and first download walkthrough |

### Commands

| Document | Description |
| --- | --- |
| [Commands Overview](commands/overview.md) | Command hierarchy and global options (`--version`, `--help`) |
| [init](commands/init.md) | Create configuration file with all options |
| [doctor](commands/doctor.md) | Run environment and config checks |
| [langs](commands/langs.md) | List dubbed audio languages for a video |
| [qualities](commands/qualities.md) | Show video and audio quality options for a language |
| [download](commands/download.md) | Download videos with all options, status display, and examples |
| [config](commands/config.md) | `config show` and `config remove` subcommands |

### Configuration

| Document | Description |
| --- | --- |
| [Configuration Overview](configuration/overview.md) | Config file format, location, CLI override behavior, and environment variables |
| [Config Keys](configuration/config-keys.md) | Complete reference for all config keys with defaults and CLI overrides |
| [Config Management](configuration/management.md) | Show, remove, and recreate config, plus validation rules |

### Usage Examples

| Document | Description |
| --- | --- |
| [Usage Examples Overview](usage-examples/index.md) | Index of all practical, production-grade usage examples |
| [Basic Downloads](usage-examples/basic-downloads.md) | Simple download operations, quality and language selection, dry runs |
| [Language and Dubs](usage-examples/language-and-dubs.md) | Language listing, resolution, region variants, fallback behavior |
| [Quality and Format](usage-examples/quality-and-format.md) | Resolution presets, audio bitrate tiers, format inspection |
| [Configuration](usage-examples/configuration.md) | Setting, showing, and managing config, CLI overrides |
| [Batch and Multiple URLs](usage-examples/batch-and-playlists.md) | Downloading multiple videos, scripting, failure handling |
| [Troubleshooting](usage-examples/troubleshooting.md) | Common errors and fixes, doctor checks, debug logging |

### Architecture

| Document | Description |
| --- | --- |
| [Architecture Overview](architecture/overview.md) | Full project directory tree |
| [Module Responsibilities](architecture/modules.md) | Detailed breakdown of every source module |
| [Download Pipeline](architecture/download-pipeline.md) | Data flow, staging system, finalization, and signal handling |
| [Test Architecture](architecture/testing.md) | Test design, file coverage, and CI pipeline |

### Features

| Document | Description |
| --- | --- |
| [Language Resolution](features/language-resolution.md) | Language-first workflow, resolution algorithm, code formats |
| [Quality Selection](features/quality-selection.md) | Video and audio quality presets, exact resolution, inspection |
| [Download Modes](features/download-modes.md) | Video mode and audio mode behavior |
| [Output Layout](features/output-layout.md) | Consistent directory structure and filename rules |
| [Staged Downloads](features/staged-downloads.md) | Crash-safe staging, atomic finalization, file exists behavior |
| [Other Features](features/other-features.md) | Dry run, disk estimation, network retry, progress display, verbose/debug modes |

### FAQ

| Document | Description |
| --- | --- |
| [General](faq/general.md) | Tool purpose, yt-dlp comparison, platform and Python requirements |
| [Installation and Setup](faq/installation-and-setup.md) | Node.js requirement, config errors, resetting config |
| [Language and Dubs](faq/language-and-dubs.md) | Language codes, availability, fuzzy matching, skipped tracks |
| [Quality and Downloads](faq/quality-and-downloads.md) | Quality recommendations, audio-only mode, output formats, file locations |
| [Troubleshooting](faq/troubleshooting.md) | Common errors, stuck downloads, debug mode, staging directory |
| [Usage and Development](faq/usage-and-development.md) | Scripting, cron, testing, linting, coverage, contributing, known limitations |

## Quick Reference

```bash
# Install (recommended)
pipx install dubbed-video-downloader
# pip install dubbed-video-downloader   # alternative

# Setup
dbdvdl init              # Create config (~/.config/dubbed-video-downloader/config.yaml)
dbdvdl doctor            # Verify everything is ready

# Explore
dbdvdl langs URL         # List available dub languages
dbdvdl qualities URL     # Show video and audio quality options

# Download
dbdvdl download URL      # Download with default language
dbdvdl download URL --lang fr --video-quality 1080p
```

## Command Overview

```
dbdvdl
├── init                     Create configuration file
├── doctor                   Run environment and config checks
├── langs URL                List dubbed audio languages for a video
├── qualities URL            Show video and audio quality options for a language
├── download URL...          Download one or more videos
├── config
│   ├── init                 Create configuration file (alias for dbdvdl init)
│   ├── show                 Print current configuration
│   └── remove               Remove the config directory
└── --version                Show version and exit
```
