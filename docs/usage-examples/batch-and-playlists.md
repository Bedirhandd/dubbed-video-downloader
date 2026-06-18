# Batch and Multiple URLs

Examples for downloading multiple videos in a single command. Each URL is processed independently with shared settings; if one fails, the rest continue.

## Downloading Multiple URLs

Pass multiple URLs to the `download` command as positional arguments:

```bash
dbdvdl download \
  "https://www.youtube.com/watch?v=ID_ONE" \
  "https://www.youtube.com/watch?v=ID_TWO" \
  "https://www.youtube.com/watch?v=ID_THREE"
```

All URLs share the same options (language, quality, mode, etc.):

```bash
dbdvdl download \
  "https://www.youtube.com/watch?v=ID_ONE" \
  "https://www.youtube.com/watch?v=ID_TWO" \
  --lang ja --video-quality 1080p
```

## Processing Behavior for Multiple URLs

- URLs are processed **sequentially** (one at a time, in the order given)
- Each URL goes through the full download pipeline independently
- If one URL fails, processing continues with the next URL
- The exit code is `1` if **any** URL failed, `0` only if all succeeded
- Output goes to separate directories per video (each video gets `language/channel/title/`)

Visual output for multiple downloads:

```
==> Downloading: https://www.youtube.com/watch?v=ID_ONE
[ok] Checking configuration...
[ok] Fetching metadata...
...
Finished
Saved to ~/Downloads/dbdvdl-output/ja/ChannelOne/TitleOne/TitleOne.mkv
Size: 250 MB

==> Downloading: https://www.youtube.com/watch?v=ID_TWO
[ok] Checking configuration...
...
Finished
Saved to ~/Downloads/dbdvdl-output/ja/ChannelTwo/TitleTwo/TitleTwo.mkv
Size: 180 MB
```

## Handling Failures Across Multiple URLs

When one URL fails, the error is printed and processing moves to the next:

```bash
dbdvdl download \
  "https://www.youtube.com/watch?v=GOOD_ID" \
  "https://www.youtube.com/watch?v=BAD_ID" \
  "https://www.youtube.com/watch?v=ANOTHER_GOOD_ID"
```

Example output:

```
==> Downloading: https://www.youtube.com/watch?v=GOOD_ID
Finished
Saved to ~/Downloads/dbdvdl-output/en/Channel/Good Video/Good Video.mkv
Size: 200 MB

==> Downloading: https://www.youtube.com/watch?v=BAD_ID
Error: Requested dub language not found.
Requested: ja
Available: en

==> Downloading: https://www.youtube.com/watch?v=ANOTHER_GOOD_ID
Finished
Saved to ~/Downloads/dbdvdl-output/en/Channel/Another Good/Another Good.mkv
Size: 150 MB
```

The exit code is `1` because one URL failed.

## Using Dry Run with Multiple URLs

Preview all URLs before downloading:

```bash
dbdvdl download \
  "https://www.youtube.com/watch?v=ID_ONE" \
  "https://www.youtube.com/watch?v=ID_TWO" \
  --dry-run
```

Each URL's plan is printed:

```
==> Dry run: https://www.youtube.com/watch?v=ID_ONE
Dry run: no files will be downloaded or created.
Title: Video One
...
Dry run OK

==> Dry run: https://www.youtube.com/watch?v=ID_TWO
Dry run: no files will be downloaded or created.
Title: Video Two
...
Dry run OK
```

## Combining with Disk Usage Confirmation

When `ask_for_disk_usage` is enabled in config, each URL prompts separately:

```bash
dbdvdl download \
  "https://www.youtube.com/watch?v=ID_ONE" \
  "https://www.youtube.com/watch?v=ID_TWO"
```

Each video gets its own confirmation prompt:

```
==> Downloading: https://www.youtube.com/watch?v=ID_ONE
This download is estimated to use ~250 MB of disk space. Continue? [y/N]: y
...

==> Downloading: https://www.youtube.com/watch?v=ID_TWO
This download is estimated to use ~180 MB of disk space. Continue? [y/N]: n
Cancelled
```

Answering `n` cancels just that one URL and continues to the next. Use `--yes` to approve all:

```bash
dbdvdl download \
  "https://www.youtube.com/watch?v=ID_ONE" \
  "https://www.youtube.com/watch?v=ID_TWO" \
  --yes
```

## Same Video, Different Languages

Download multiple language tracks of the same video:

```bash
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ko
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr --mode audio
```

Output layout:

```
~/Downloads/dbdvdl-output/ja/<channel>/<title>/<title>.mkv
~/Downloads/dbdvdl-output/ko/<channel>/<title>/<title>.mkv
~/Downloads/dbdvdl-output/fr/<channel>/<title>/<title>.webm
```

Since each language produces a different output path, there is no conflict -- even without `--if-exists overwrite`.

## Same Video, Different Qualities

Downloading the same video with different quality settings will overwrite (if using `--if-exists overwrite`) or be skipped (the default):

```bash
# First download: best quality
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality best

# Second download: low quality -- skipped because file already exists
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality low
# Output: Skipped — Output already exists: ...

# To actually download a different quality, use --if-exists overwrite
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --video-quality low --if-exists overwrite
```

## Scripting with Multiple URLs

For scripts that process a list of URLs, use `--yes` and `--if-exists skip` for non-interactive operation:

```bash
#!/bin/bash
# Download multiple videos non-interactively
dbdvdl download \
  "https://www.youtube.com/watch?v=ID_ONE" \
  "https://www.youtube.com/watch?v=ID_TWO" \
  "https://www.youtube.com/watch?v=ID_THREE" \
  --lang ja \
  --video-quality 1080p \
  --if-exists skip \
  --yes

if [ $? -ne 0 ]; then
  echo "Some downloads failed. Check the output above."
fi
```

## Current Limitations

Note the following about the current version (0.2.0):

- **No playlist support:** The `download` command accepts individual video URLs only. YouTube playlist URLs will not be expanded automatically. For playlists, extract individual video URLs first (e.g., using `yt-dlp --flat-playlist --print url <playlist_url>`) and pass them to `dbdvdl download`.
- **No channel support:** Channel URLs are not automatically expanded to individual videos.
- **No text file input:** There is no `--batch-file` or `--input-file` option. Instead, use shell features to read from a file:

```bash
# Read URLs from a file (one URL per line) and pass as arguments
xargs dbdvdl download --lang ja --yes < urls.txt

# Or using a shell loop for more control
while IFS= read -r url; do
  [ -z "$url" ] && continue
  dbdvdl download "$url" --lang ja --yes || echo "Failed: $url"
done < urls.txt
```

- **Sequential only:** Downloads are always sequential (one at a time). There is no concurrent/parallel download mode.

## Next Steps

- [Basic Downloads](basic-downloads.md) -- Single video download workflows
- [Language and Dubs](language-and-dubs.md) -- Language selection and resolution
- [Troubleshooting](troubleshooting.md) -- Handling errors during batch operations
