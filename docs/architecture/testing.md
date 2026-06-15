# Test Architecture

## Test Design

- **Offline by default:** `tests/support/network_guard.py` monkey-patches `socket.socket.connect`, `connect_ex`, and `create_connection` to block all TCP connections during test execution
- **Opt-out for debugging:** Set `DBDVDL_TESTS_ALLOW_NETWORK=1` to disable the guard
- **Session-scoped guard:** Installed once per test session via `conftest.py` autouse fixture
- **Typer CLI testing:** Uses `typer.testing.CliRunner` for testing CLI commands with stdin/stdout capture
- **Path isolation:** Tests use `tmp_path` for config files, output directories, and staging

## Test File Coverage

| Test File | Focus |
| --- | --- |
| `test_config.py` | Config loading, validation, normalization, missing keys, invalid values |
| `test_languages.py` | Language code normalization, video tag collection, language resolution, fuzzy matching |
| `test_quality.py` | Video/audio quality normalization, format selector construction, quality selection |
| `test_cli_init.py` | `init` command with various options, force overwrite, defaults |
| `test_cli_config_commands.py` | `config show`, `config remove` commands |
| `test_cli_langs.py` | `langs` command with mocked metadata |
| `test_cli_qualities.py` | `qualities` command with mocked metadata |
| `test_cli_download.py` | `download` command end-to-end, dry-run, exists behavior, error handling |
| `test_core_video_info.py` | Metadata extraction, language listing |
| `test_core_download.py` | Download orchestration with mocked yt-dlp |
| `test_core_plan_download.py` | Plan download (dry-run) logic |
| `test_core_finalize.py` | Staged download finalization, hard links, cross-filesystem copies, no-clobber publish |
| `test_core_stale_cleanup.py` | Stale incomplete download cleanup |
| `test_core_exists_behavior.py` | Output file exists handling (skip/fail/overwrite) |
| `test_doctor.py` | Doctor check functions, executable resolution, command checks |
| `test_errors.py` | Exception hierarchy, error message formatting |
| `test_network_guard.py` | Network guard installation and behavior |

## CI Pipeline

The CI pipeline (`.github/workflows/ci.yml`) runs on push to `main` and `feat/cli`, and on all PRs:

1. **Lint job (Python 3.12):**
   - `ruff check` with GitHub output format
   - `ruff format --check`
   - `mypy` with strict mode

2. **Test job matrix (Python 3.10, 3.11, 3.12):**
   - `pytest` with coverage collection
   - Coverage report, XML export, and threshold enforcement (--fail-under=79)
   - Coverage artifacts uploaded with 7-day retention
