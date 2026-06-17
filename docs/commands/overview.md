# Commands Overview

This document covers the command hierarchy and global options available in `dbdvdl`. After a PyPI install, run `dbdvdl` directly. When working from a git checkout, use `uv run dbdvdl` instead (see [Installation](../getting-started/installation.md#install-from-source)).

## Command Hierarchy

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

## Global Options

### `--version`

Show the version and exit immediately. This option is eager -- it is processed before any other option or command.

```
dbdvdl --version
```

Output:

```
dbdvdl 0.2.0
```

### `--help`

Show help for any command. Available on the root app and every subcommand.

```
dbdvdl --help
dbdvdl download --help
dbdvdl config --help
```
