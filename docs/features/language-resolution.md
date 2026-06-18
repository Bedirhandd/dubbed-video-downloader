# Language-First Workflow

The core design principle of Dubbed Video Downloader is language-first: before you commit to a download, you can inspect what dub languages are available.

## Listing Available Languages

The `langs` command scans a video's audio format metadata and returns all valid language tags. It filters out:
- Audio tracks missing language metadata
- Tracks with invalid BCP-47 language tags
- Tracks tagged as `und` (undefined)

## Language Resolution

When you provide a language code (e.g., `--lang fr`), the system performs a multi-step resolution against the video's audio tracks:

1. **Exact match:** Your canonical BCP-47 code (after standardization) is matched case-insensitively against raw metadata tags. For example, requesting `en` matches both `en` and `en-US` in the metadata.

2. **Fuzzy match (variant only):** If no exact match exists and you did not specify a territory or script (i.e., you requested just `fr`, not `fr-FR`), the system uses `langcodes.closest_supported_match()` with a maximum variant distance of 10. This handles cases where the metadata uses a related but not identical language tag.

3. **Exact required (territory/script):** If your request includes a territory (e.g., `pt-BR`) or script (e.g., `zh-Hans`), only an exact match is accepted. No fuzzy matching occurs.

4. **Error:** If no match is found, a `LanguageNotFoundError` is raised with the list of available languages.

## Language Code Formats

Supported formats for user input:

| Format | Example | Notes |
| --- | --- | --- |
| Two-letter | `en`, `ja`, `ko`, `tr` | Most common format |
| Three-letter | `eng`, `jpn`, `kor` | ISO 639-3 codes |
| With region | `en-US`, `pt-BR`, `es-MX` | Requires exact match |
| With script | `zh-Hans`, `zh-Hant` | Requires exact match |

All codes are validated and standardized using the `langcodes` library before use.
