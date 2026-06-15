# Organized Output

All downloads follow a consistent directory structure:

```
output_dir/
└── <language>/
    └── <channel>/
        └── <title>/
            └── <title>.<ext>
```

For example, downloading a French dub of a video by "CookingChannel" titled "Pasta Recipe":

```
~/Downloads/dbdvdl-output/fr/CookingChannel/Pasta Recipe/Pasta Recipe.mkv
```

Key properties:
- **Predictable:** You always know where your files will land
- **Language-separated:** Each language gets its own top-level directory
- **Channel-organized:** Files grouped by uploader
- **Title-preserving:** Uses the original video title (sanitized for filesystem compatibility)
- **Restricted filenames:** The `restrictfilenames` option is enabled for yt-dlp, limiting characters to ASCII for portability
