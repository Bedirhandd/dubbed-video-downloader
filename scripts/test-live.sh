#!/usr/bin/env sh
set -eu

if [ -z "${DBDVDL_LIVE_TEST_URL:-}" ]; then
  echo "DBDVDL_LIVE_TEST_URL is required." >&2
  echo "Provide a public YouTube URL with multiple dubbed audio options." >&2
  echo "Preferably 2 to 5 minutes long; longer videos are acceptable but slower." >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg is required for live integration tests." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required for live integration tests." >&2
  exit 1
fi

export DBDVDL_TESTS_ALLOW_NETWORK=1

# Optional: set DBDVDL_LIVE_MATRIX=1 to also run the long audio/video quality
# matrix (12 real downloads). See CONTRIBUTING.md.

exec uv run pytest tests/live -m live -v "$@"
