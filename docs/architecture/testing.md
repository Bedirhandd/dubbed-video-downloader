# Test Architecture

## Test Design

- **Offline by default:** `tests/support/network_guard.py` monkey-patches `socket.socket.connect`, `connect_ex`, and `create_connection` to block all TCP connections during test execution
- **Opt-out for debugging:** Set `DBDVDL_TESTS_ALLOW_NETWORK=1` to disable the guard
- **Live integration (local only):** `tests/live/` contains `@pytest.mark.live` tests that require `DBDVDL_LIVE_TEST_URL` and real YouTube access; run them with `./scripts/test-live.sh`
- **Live quality matrix (opt-in):** `@pytest.mark.live_matrix` tests in `tests/live/test_live_matrix.py` run only when `DBDVDL_LIVE_MATRIX=1`; each download uses an isolated temp dir that is removed after the test
- **Default pytest selection:** `--ignore=tests/live` excludes live tests from the offline gate and CI
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
| `tests/live/test_live_metadata.py` | Live metadata, langs, qualities, dry-run (local only) |
| `tests/live/test_live_download.py` | Live audio/video download and error paths (local only) |
| `tests/live/test_live_matrix.py` | Opt-in live quality matrix across audio/video presets (local only) |

## CI Pipeline

The CI pipeline (`.github/workflows/ci.yml`) runs on push to `main` and `feat/cli`, and on all PRs:

1. **Lint job (Python 3.12):**
   - `ruff check` with GitHub output format
   - `ruff format --check`
   - `mypy` with strict mode

2. **Audit job:**
   - `uv audit --frozen --preview-features audit` against `uv.lock` (runtime and dev dependencies)
   - Negative self-check using `tests/fixtures/vulnerability-audit-negative/` to verify the scanner fails on known CVEs

3. **Test job matrix (Python 3.10, 3.11, 3.12):**
   - `pytest --ignore=tests/live` with coverage collection
   - Coverage report, XML export, and threshold enforcement (--fail-under=79)
   - Coverage artifacts uploaded with 7-day retention

Live integration tests are excluded from CI. Run them locally before relevant pull
requests with `./scripts/test-live.sh` (see [CONTRIBUTING.md](../../CONTRIBUTING.md)).
