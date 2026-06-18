# Troubleshooting

## I get "Could not extract video metadata". What does this mean?

yt-dlp was unable to fetch video information from YouTube. Possible causes:

- **Invalid URL:** Make sure the URL is a valid YouTube video URL
- **Network issues:** Check your internet connection
- **YouTube changes:** YouTube may have updated its page structure. Try upgrading the package: `pipx upgrade dubbed-video-downloader` or `pip install -U dubbed-video-downloader`
- **Geographic restrictions:** The video may be unavailable in your region

## I get "Requested dub language not found".

The language you requested is not available on this video. Run `dbdvdl langs URL` to see what languages are available.

## I get "Config error: Config file not found".

Run `dbdvdl init` to create the configuration file.

## The download seems stuck. What should I do?

- Try with `--verbose` to see yt-dlp's output
- Try with `--debug` to see full debug output and tracebacks
- Check your internet connection
- Try a different video to see if the issue is specific to one URL

## How do I get more detailed error information?

Use the `--debug` flag:

```bash
dbdvdl download "URL" --debug
```

This shows yt-dlp's debug output and, on error, the full Python traceback.

## Files are accumulating in tmp/.incomplete/. What is this?

This is the staging directory for downloads in progress. If a download is interrupted (crash, kill signal, power loss), the incomplete files remain here. They are automatically cleaned up the next time you run a download. You should not need to manually manage this directory.
