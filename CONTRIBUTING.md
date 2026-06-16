# Contributing

Contributions are welcome, and issues are welcome too. Thanks for helping improve this project.

This project follows the Conventional Commits style. See the specification here:
https://www.conventionalcommits.org/en/v1.0.0/

## For Humans

- Use commit messages in this format: `<type>(<scope>): <description>`
- Use branch names in this format: `<type>/<short-description>`
- Use pull request titles in the same format as commit messages: `<type>(<scope>): <description>`
- Keep pull requests focused on one change when possible.
- Include a short description of what changed and how it was tested.
- Open an issue for bugs, questions, suggestions, or improvements.

### Fork Workflow

If you do not have write access to this repository:

1. Fork the repository to your GitHub account.
2. Clone your fork locally.
3. Create a branch using the project branch naming format: `<type>/<short-description>`
4. Make your changes and commit them using the project commit message format: `<type>(<scope>): <description>`
5. Push your branch to your fork.
6. Open a pull request from your fork branch to this repository.

Before opening a pull request, make sure your branch is up to date with the target branch and include a short note about what changed and how you checked it.

## Testing

The automated test suite is fully offline by default. A network guard blocks TCP socket
connections during test execution unless you explicitly opt out for local debugging
with `DBDVDL_TESTS_ALLOW_NETWORK=1`.

Install dev dependencies and run the full quality gate:

```bash
uv sync --group dev
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy
uv audit --frozen --preview-features audit
uv run pytest --cov=dubbed_video_downloader --cov-report=term -v
uv run coverage report --fail-under=79
```

The default `pytest` invocation excludes live integration tests (`--ignore=tests/live`).
CI runs the same offline gate only.

### Live integration (local only)

Before opening a pull request that changes download, yt-dlp, language, quality,
planning, or FFmpeg-facing behavior, run the live integration suite locally with a
real YouTube URL. CI does not run these tests and the URL must not be committed.

Choose a video that is:

- preferably **2 to 5 minutes** long (longer is acceptable but slower)
- public and accessible without login or age restriction
- stable enough for repeat runs
- equipped with **multiple dubbed audio options** so language discovery and selection
  can be validated end to end
- suitable for low-quality audio and video downloads during the suite

Run the suite with the wrapper script:

```bash
DBDVDL_LIVE_TEST_URL='https://www.youtube.com/watch?v=VIDEO_ID' ./scripts/test-live.sh
```

Optional overrides:

- `DBDVDL_LIVE_TEST_LANG` — force a specific dub language from the video
- additional pytest args are forwarded to the live command, for example
  `./scripts/test-live.sh -k metadata`

Include the live-test result in your pull request description under “how it was
tested”. Mention the video ID or URL you used locally.

### Pre-commit hooks

Install hooks once after syncing dev dependencies:

```bash
uv sync --group dev
uv run pre-commit install
uv run pre-commit run --all-files
```

Platform-specific tests may use `@pytest.mark.skip` or `pytest.skip()` on unusual filesystem layouts; skips are expected and do not fail CI.

The coverage gate in CI uses `--fail-under=79`, which must stay in sync with `fail_under` in `pyproject.toml`.

Examples:

```text
docs(readme): add setup notes
fix(download): handle missing dub language
chore(deps): update yt-dlp
```

```text
docs/update-readme
fix/missing-dub-language
chore/update-yt-dlp
```

## For Agents

- Follow the same commit, branch, and pull request naming conventions used by humans.
- Keep edits scoped to the requested task.
- Prefer small, reviewable documentation or code changes.
- Do not rewrite unrelated files or revert user changes.
- Mention the checks, tests, or manual verification performed.
- If something cannot be verified, state that clearly in the pull request or response.
- When live integration verification is required, **explicitly ask the user for a real
  YouTube video URL** before running `./scripts/test-live.sh`. Request a video that is:
  - preferably **2 to 5 minutes** long (longer is acceptable but slower)
  - public and accessible without login or age restriction
  - equipped with **multiple dubbed audio options**
  - suitable for end-to-end language, quality, and download validation
- Do not commit the live-test URL to the repository.
