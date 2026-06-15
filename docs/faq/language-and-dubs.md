# Language and Dubs FAQ

## How do I find out what dub languages a video has?

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"
```

## What language codes can I use?

Any valid BCP-47 language code. Common formats:

- Two-letter: `en`, `ja`, `ko`, `tr`, `es`, `fr`, `de`
- Three-letter: `eng`, `jpn`, `kor`
- With region: `en-US`, `pt-BR`

The code is validated and standardized using the `langcodes` library.

## What happens if the language I want is not available?

The command fails with a `LanguageNotFoundError` listing all available languages. You can check available languages with `dbdvdl langs` before downloading.

## What if YouTube uses a different language tag than what I expect?

The system performs fuzzy matching without requiring exact tag format. For example, if YouTube uses `en-US` in the metadata and you request `en`, the system will match them. Requests with territory or script (e.g., `zh-Hans`) require an exact match.

## Why do some audio tracks get skipped with a warning?

Some YouTube videos have audio tracks with missing or invalid language metadata. These tracks are skipped with a warning like:

```
Skipped 2 audio track(s) with invalid or undefined language metadata.
```

This does not prevent you from downloading the valid tracks.
