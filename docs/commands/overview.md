# Commands Overview

This document covers the command hierarchy and global options available in `dbdvdl`. All commands are run via `uv run dbdvdl` or, if installed as a global tool, `dbdvdl`.

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
uv run dbdvdl --version
```

Output:

```
dbdvdl 0.1.0
```

### `--help`

Show help for any command. Available on the root app and every subcommand.

```
uv run dbdvdl --help
uv run dbdvdl download --help
uv run dbdvdl config --help
```
