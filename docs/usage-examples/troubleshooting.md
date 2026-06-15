# Troubleshooting Examples

Practical troubleshooting scenarios -- common errors, their causes, and step-by-step solutions. Also covers environment verification with the `doctor` command.

## Verifying Your Setup

Before troubleshooting download issues, confirm your environment is correctly configured:

```bash
uv run dbdvdl doctor
```

Expected output when everything is OK:

```
System check

Python          OK     3.10.12
Config          OK     /home/user/.config/dubbed-video-downloader/config.yaml
Config permissions OK    owner-only permissions
Output directory OK    /home/user/Downloads/dbdvdl-output exists and is writable
FFmpeg          OK     7.0.2-3ubuntu1 (/usr/bin/ffmpeg)
Node            OK     v22.14.0 (/usr/bin/node)
yt-dlp          OK     2026.3.17
yt-dlp-ejs      OK     0.8.0
```

The `doctor` command exits with code `1` if any check fails, `0` if all pass. The `Config permissions` check can show a warning in its detail while still reporting `OK`.

## Doctor Check Failures and Fixes

### Config Permissions Warning (Not a Failure)

```
Config permissions OK    permissions are not owner-only; recommended chmod 600 config.yaml and chmod 700 /home/user/.config/dubbed-video-downloader
```

**Cause:** The config file or directory is readable by other users on a POSIX system. This often happens with configs created before owner-only modes were enforced, or after manual edits.

**Fix:** Apply the suggested `chmod` commands, or recreate the config:

```bash
chmod 700 ~/.config/dubbed-video-downloader
chmod 600 ~/.config/dubbed-video-downloader/config.yaml
```

Alternatively:

```bash
uv run dbdvdl init --force --default
```

Downloads continue to work while the warning is present; tightening permissions is recommended on shared or multi-user systems.

### Python Version Too Old

```
Python          FAIL   3.9.18
```

**Cause:** Python 3.10+ is required.

**Fix:** Install Python 3.10 or newer.

### Config Missing

```
Config          FAIL    Config file not found at /home/user/.config/dubbed-video-downloader/config.yaml. Run `dbdvdl init` to create it.
```

**Cause:** You have not run `dbdvdl init` yet, or the config was removed.

**Fix:**

```bash
uv run dbdvdl init
```

### Config Parsing Error

```
Config          FAIL    Could not parse /home/user/.config/dubbed-video-downloader/config.yaml: ...
```

**Cause:** The YAML file has a syntax error (likely from manual editing).

**Fix:** Open the file and fix the YAML syntax, or recreate it:

```bash
uv run dbdvdl init --force --default
```

### Output Directory Not Writable

```
Output directory FAIL    /home/user/Downloads/dbdvdl-output is not writable
```

**Cause:** Permissions issue on the output directory.

**Fix:**

```bash
chmod u+w ~/Downloads/dbdvdl-output
```

Or change to a different directory:

```bash
uv run dbdvdl init --force --output-dir ~/Videos/dubbed
```

### FFmpeg Not Found

```
FFmpeg          FAIL    ffmpeg was not found on PATH
```

**Cause:** FFmpeg is not installed or not on your PATH.

**Fix (Ubuntu/Debian):**

```bash
sudo apt install ffmpeg
```

**Fix (using a custom path if installed elsewhere):**

```bash
uv run dbdvdl init --force --ffmpeg-path /usr/local/bin/ffmpeg
```

### Node.js Not Found

```
Node            FAIL    node was not found on PATH
```

**Cause:** Node.js is required by `yt-dlp-ejs` for YouTube's JavaScript solver.

**Fix:** Install Node.js 18+.

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install nodejs

# Or use nvm
nvm install 22
nvm use 22
```

### yt-dlp or yt-dlp-ejs Not Installed

```
yt-dlp          FAIL    package is not installed
```

**Cause:** Dependencies were not synced correctly.

**Fix:**

```bash
uv sync
```

## Download-Specific Errors

### "Config file not found"

```
Error: Config file not found at /home/user/.config/dubbed-video-downloader/config.yaml. Run `dbdvdl init` to create it.
```

This happens with any command (`download`, `langs`, `qualities`) when the config file is missing.

**Fix:**

```bash
uv run dbdvdl init
```

### "Could not extract video metadata"

```
Error: Could not extract video metadata: ...
```

**Common causes:**

1. **Invalid URL:** Make sure the URL is a valid YouTube video URL (`https://www.youtube.com/watch?v=...`) using `http` or `https` with a host. Non-HTTP(S) schemes such as `file://` are rejected by the CLI before yt-dlp runs.
2. **Network issues:** Check your internet connection
3. **YouTube changes:** YouTube may have updated its page structure

**Diagnosis steps:**

```bash
# Test with --debug for full details
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --debug

# Try a different, well-known video
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"

# Check if yt-dlp itself can access the video
uv run yt-dlp --print title "https://www.youtube.com/watch?v=VIDEO_ID"
```

**If yt-dlp works but dbdvdl doesn't:** This may indicate a version mismatch. Update dependencies:

```bash
uv sync --upgrade-package yt-dlp
```

### "Requested dub language not found"

```
Error: For 'Video Title': Requested dub language not found.
Requested: fr
Available: en, ja, ko
```

**Cause:** The language you requested is not available on this video.

**Fix:** List available languages and choose one:

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"
# Output: en, ja, ko
```

Then download with an available language:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja
```

### "Requested video quality Np is not available"

```
Input error: Requested video quality 480p is not available. Available video qualities: 144p, 360p, 720p, 1080p.
```

**Cause:** The exact resolution you requested is not among the video's available heights.

**Fix:** Inspect available qualities and pick one:

```bash
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja

# Then use an available quality or a preset
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja --video-quality 720p
# Or use a preset that always works
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja --video-quality best
```

### "No audio streams found for language"

```
Error: No audio streams found for language `ja`.
```

**Cause:** `langs` listed a language, but `qualities` can't find audio streams matching that exact metadata tag. This can happen if the language tag used by the audio track differs from what `langs` normalized.

**Fix:** Use exact match or inspect the language resolution:

```bash
# Check what quality options exist (this shows resolved vs requested language)
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja

# Try without specifying lang to use config default
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID"
```

### "Output already exists"

```
Error: Output already exists: ~/Downloads/dbdvdl-output/en/Channel/Title/Title.mkv
```

**Cause:** The planned output file already exists and `--if-exists fail` is set.

**Fix:** Choose a different behavior:

```bash
# Skip existing files
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --if-exists skip

# Overwrite existing files
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --if-exists overwrite
```

### "Output path already exists but is not a file"

```
Error: Output path already exists but is not a file: ~/Downloads/dbdvdl-output/en/Channel/Title/Title.mkv
```

**Cause:** The path where the output file should be is a directory (e.g., from a previous manual operation) or a symlink.

**Fix:** Remove or rename the conflicting path:

```bash
ls -la "~/Downloads/dbdvdl-output/en/Channel/Title/"
# If "Title.mkv" is a directory:
rmdir "~/Downloads/dbdvdl-output/en/Channel/Title/Title.mkv"
```

### "Could not download media"

```
Error: Could not download media: ...
```

**Cause:** yt-dlp encountered an error during the actual download. The specific error message from yt-dlp is included.

**Diagnosis:**

```bash
# Run with --debug to see the full yt-dlp output and traceback
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --debug

# Check if the video is accessible at all
uv run yt-dlp --print title "https://www.youtube.com/watch?v=VIDEO_ID"

# Check for regional restrictions
uv run yt-dlp --dump-json "https://www.youtube.com/watch?v=VIDEO_ID" | python3 -m json.tool | grep -A2 restriction
```

## Diagnosing with Verbose and Debug Modes

### Verbose: See yt-dlp Output

When the default status display hides useful information:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

This shows yt-dlp's progress bar, info messages, and warnings instead of the minimal status spinner. Use this when:
- A download seems stuck and you want to see what's happening
- You want to monitor download speed and progress in detail
- You want to see yt-dlp's format selection process

### Debug: Maximum Detail

For the deepest level of information:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --debug
```

This shows:
- yt-dlp's debug log output
- Full Python traceback on any error (sent to stderr)

Use this when:
- You need to report a bug
- A download fails with a generic error message
- You want to see the full yt-dlp format negotiation

### Verbose + Debug Combined

`--debug` is a superset of `--verbose`. You only need one:

```bash
# Just verbose output
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --verbose

# Verbose + debug tracebacks
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --debug
```

## Staging Directory (`tmp/.incomplete/`)

### Files Accumulating in tmp/.incomplete/

If you notice files building up in `~/Downloads/dbdvdl-output/tmp/.incomplete/`:

**Normal behavior:** This is the staging directory for downloads in progress. During a download, partial files live here until the download completes successfully. Upon completion, files are moved to the final output location and the staging directory is cleaned up.

**If files remain after a crash:** The system automatically cleans stale staging directories the next time you run a download. No manual intervention is needed.

**To manually clean up:**

```bash
# Check what's there
ls -la ~/Downloads/dbdvdl-output/tmp/.incomplete/

# If you're sure no downloads are in progress, remove everything
rm -rf ~/Downloads/dbdvdl-output/tmp/.incomplete/*
```

**WARNING:** Do not remove the `tmp/.incomplete/` directory while a download is running.

### Stale Finalizing Copy Directories

If you see `.dubbed-video-downloader-finalizing/` directories in your output paths:

```
~/Downloads/dbdvdl-output/en/Channel/Title/.dubbed-video-downloader-finalizing/
```

These are remnants of an interrupted finalization. The next `dbdvdl download` run will clean them up automatically. You can also safely remove them manually if no download is in progress:

```bash
find ~/Downloads/dbdvdl-output -name ".dubbed-video-downloader-finalizing" -type d -exec rm -rf {} +
```

## Network and Connectivity Issues

### Downloads Keep Failing on Unstable Connections

Increase the retry count:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --retry-on-network-failure 10 \
  --verbose
```

Retries use exponential backoff (max 8 seconds between attempts with jitter), so increasing the count helps with intermittent connectivity.

### DNS or Proxy Issues

If yt-dlp can't resolve YouTube, check if the issue is with your network:

```bash
# Test basic connectivity
curl -I https://www.youtube.com

# Test yt-dlp directly
uv run yt-dlp --print title "https://www.youtube.com/watch?v=VIDEO_ID"

# If using a proxy, configure yt-dlp via environment variables
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

## Understanding Disk Usage Prompts in Scripts

If you're running `dbdvdl` from a script and it refuses to run:

```
Refusing to download non-interactively with disk usage confirmation enabled. Use --yes to approve.
```

**Cause:** `ask_for_disk_usage` is set to `true` in your config, and stdin is not a TTY.

**Fix:** Either disable disk usage prompts or use `--yes`:

```bash
# Option 1: Add --yes to the command
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --yes

# Option 2: Disable disk usage prompts in config
uv run dbdvdl init --force --default --no-ask-for-disk-usage
```

## Debugging Language Resolution Issues

If a language you expect to be available isn't matching:

```bash
# 1. See raw language tags
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"

# 2. Try the exact tag shown in the output
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang es-419

# 3. Check quality options with that language to confirm it resolves
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja
```

The `qualities` output shows both `Language:` (what you requested) and `(track: <resolved>)` if the resolved track differs from your request.

## Next Steps

- [Basic Downloads](basic-downloads.md) -- Getting back to working downloads
- [Configuration](configuration.md) -- Fixing config-related issues
- [Quality and Format](quality-and-format.md) -- Understanding quality selection errors
