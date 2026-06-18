# Security Policy

## Supported Versions

Security fixes are provided for the **latest released version** of Dubbed Video Downloader (`dbdvdl`). Older releases may not receive backported fixes.

| Version | Supported |
| ------- | --------- |
| 0.2.x   | Yes       |
| < 0.2   | No        |

Install the latest release from [PyPI](https://pypi.org/project/dubbed-video-downloader/) or the [GitHub releases](https://github.com/Bedirhandd/dubbed-video-downloader/releases) page.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

This repository uses [GitHub Private Vulnerability Reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability). To report a vulnerability:

1. Open the repository's **Security** tab on GitHub.
2. Click **Report a vulnerability**.
3. Submit a private advisory with the details below.

Direct link: [Report a vulnerability](https://github.com/Bedirhandd/dubbed-video-downloader/security/advisories/new)

If you cannot use GitHub's reporting flow, you may contact the maintainer through the contact information on their GitHub profile. Do not disclose the vulnerability publicly until we have had a chance to address it.

### Dependency Issues

Dependabot monitors this repository's dependencies and opens pull requests for security fixes and scheduled version updates (see [Project Security Maintenance](#project-security-maintenance)). Configuration lives in [`.github/dependabot.yml`](.github/dependabot.yml).

If Dependabot has not opened a pull request yet, or you notice a dependency concern it missed in this repository (for example, a CVE affecting a Python package pinned in `uv.lock` or a GitHub Actions workflow dependency), you may [open a GitHub issue](https://github.com/Bedirhandd/dubbed-video-downloader/issues). Include the affected package, version, advisory link, and why it matters for `dbdvdl` when you can.

System tools you install separately (such as FFmpeg or Node.js) are not tracked in this repository — see [Out of Scope](#out-of-scope) for where to report those.

If the dependency issue is exploitable in typical CLI usage and you prefer private coordination, use [private vulnerability reporting](#reporting-a-vulnerability) instead.

### What to Include

A helpful report usually contains:

- A clear description of the vulnerability and its impact
- Steps to reproduce the issue, including version, OS, and configuration when relevant
- Proof-of-concept code, commands, or screenshots if available
- Any known mitigations or workarounds
- Your preferred contact method for follow-up (optional)

### What We Will Do

When we receive a valid security report, we aim to:

1. **Acknowledge** receipt within **3 business days**
2. **Investigate** and confirm the issue
3. **Develop and test** a fix
4. **Coordinate disclosure** with you before any public announcement
5. **Publish** a security advisory and patched release when a fix is ready

Timelines depend on severity and complexity. We will keep you informed of progress.

### Safe Harbor

We support good-faith security research on this project. If you follow this policy — including avoiding privacy violations, data destruction, service disruption, and public disclosure before coordination — we will not pursue legal action against you for your research.

## Scope

### In Scope

Security issues in this repository that affect users of the `dbdvdl` CLI, including but not limited to:

- Arbitrary command execution, path traversal, or unsafe file operations in this project
- Injection or unsafe handling of user-supplied input (URLs, paths, config values, CLI flags)
- Insecure defaults that expose local files, credentials, or system resources
- Dependency vulnerabilities introduced or materially worsened by this project's integration
- Issues in staging, finalization, or output-path handling that could corrupt or overwrite unintended files

### Out of Scope

The following are generally **not** handled through this security policy:

- Vulnerabilities in **system or upstream runtime tools** ([FFmpeg](https://ffmpeg.org/), [Node.js](https://nodejs.org/), the OS, and similar) unless this tool introduces a distinct, exploitable exposure. Report those to the respective upstream projects. For [yt-dlp](https://github.com/yt-dlp/yt-dlp), report upstream first; open an issue here only if the problem is specific to how `dbdvdl` integrates with it.
- Issues that require the victim to run untrusted code or binaries outside normal documented usage (for example, pointing `ffmpeg_path` at a malicious executable they deliberately installed).
- Social engineering, phishing, or physical attacks
- Denial-of-service from downloading very large media files through normal CLI use
- Bugs with no realistic security impact (cosmetic issues, feature requests, download failures due to YouTube or network changes)
- Violations of third-party terms of service (including YouTube's Terms of Service)

If you are unsure whether something is in scope, report it privately anyway and we will triage it.

## Disclosure Policy

We follow **coordinated disclosure**:

- Please allow reasonable time for a fix before public disclosure.
- We will work with you on an advisory timeline and credit (if desired) when a CVE or GitHub Security Advisory is published.
- Once a fix is released, details may be published in a GitHub Security Advisory and noted in the changelog.

## Security Practices for Users

To reduce risk when using this tool:

- **Keep software updated** — use the latest `dbdvdl` release and keep system dependencies (`ffmpeg`, `node`, `yt-dlp`) current.
- **Use trusted sources** — install from PyPI or this official repository; verify release integrity when downloading manually.
- **Protect your config** — the config file under `~/.config/dubbed-video-downloader/` may contain paths and preferences; restrict filesystem permissions as you would for other local application config.
- **Point FFmpeg to a trusted binary** — if you override `ffmpeg_path`, use an executable you installed from a trusted source.
- **Be cautious with URLs** — only download from sources you trust; untrusted video URLs are processed by yt-dlp and may trigger network fetches or extractor-specific behavior outside this project's control.
- **Review scripts that wrap the CLI** — if you automate `dbdvdl` in shell scripts or cron jobs, validate inputs before passing them to the tool.

## Project Security Maintenance

This project uses [Dependabot](https://docs.github.com/en/code-security/dependabot) together with CI checks:

| Layer | What it does |
| ----- | ------------ |
| **Dependabot alerts** | Notifies when known vulnerabilities affect repository dependencies |
| **Dependabot security updates** | Opens grouped pull requests to patch alerted vulnerabilities |
| **Dependabot version updates** | Opens scheduled pull requests to keep dependencies current (configured in [`.github/dependabot.yml`](.github/dependabot.yml): weekly `github-actions` and `uv` updates) |
| **CI (`uv audit`)** | Blocks merges when known vulnerabilities remain in `uv.lock` |

Security fixes for dependencies are prioritized alongside application fixes. Community reports via issues or private vulnerability reporting remain welcome when automation does not cover a case.

Thank you for helping keep Dubbed Video Downloader and its users safe.
