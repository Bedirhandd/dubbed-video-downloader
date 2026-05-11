from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from . import __version__
from . import core
from . import doctor

CLI_DEFAULT_OUTPUT_DIR = Path("~/Downloads/dbdvdl-output")

HELP_EPILOG = """
Examples:

  dbdvdl --doctor

  dbdvdl langs https://www.youtube.com/watch?v=VIDEO_ID

  dbdvdl download https://www.youtube.com/watch?v=VIDEO_ID --lang tr

  dbdvdl download URL1 URL2 --lang en --output-dir ~/Downloads/dbdvdl-output
"""

app = typer.Typer(
    help=(
        "Download YouTube videos with a selected dubbed audio track.\n\n"
        "Use `langs` to inspect available audio languages, then `download` with "
        "the language code you want."
    ),
    epilog=HELP_EPILOG,
    no_args_is_help=True,
    subcommand_metavar="COMMAND [URL]...",
    add_completion=False,
    rich_markup_mode="rich",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"dbdvdl {__version__}")
        raise typer.Exit()


def _doctor_callback(value: bool) -> None:
    if not value:
        return

    results = doctor.run_checks()
    name_width = max(len(result.name) for result in results)

    typer.echo("System check\n")
    for result in results:
        status = "OK" if result.ok else "Missing"
        color = typer.colors.GREEN if result.ok else typer.colors.RED
        typer.echo(f"{result.name:<{name_width}}  ", nl=False)
        typer.secho(f"{status:<7}", fg=color, nl=False)
        typer.echo(result.detail)

    if not all(result.ok for result in results):
        raise typer.Exit(code=1)

    raise typer.Exit()


def _output_dir_callback(value: Path) -> Path:
    output_dir = value.expanduser()
    if not output_dir.is_absolute():
        raise typer.BadParameter(
            "must be an absolute path. Use ~/Downloads/dbdvdl-output or /path/to/output."
        )
    return output_dir


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            help="Show the version and exit.",
            is_eager=True,
        ),
    ] = False,
    doctor_check: Annotated[
        bool,
        typer.Option(
            "--doctor",
            callback=_doctor_callback,
            help="Run environment checks and exit.",
            is_eager=True,
        ),
    ] = False,
) -> None:
    """CLI entrypoint."""


@app.command("download")
def download_command(
    urls: Annotated[
        list[str],
        typer.Argument(
            help="One or more YouTube video URLs to download.",
            metavar="URL...",
        ),
    ],
    lang: Annotated[
        str,
        typer.Option("--lang", "-l", help="Target dub language code."),
    ] = "tr",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            callback=_output_dir_callback,
            help="Absolute directory where videos will be saved. Supports ~.",
        ),
    ] = CLI_DEFAULT_OUTPUT_DIR,
    ffmpeg_path: Annotated[
        Path | None,
        typer.Option(
            "--ffmpeg-path",
            help="Path to the FFmpeg executable.",
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
) -> None:
    """Download URL(s) with a dub language."""
    failures = 0
    for url in urls:
        typer.echo(f"\n==> Downloading: {url}")
        try:
            core.download(
                url=url,
                lang=lang,
                ffmpeg_path=ffmpeg_path,
                output_dir=output_dir,
            )
            typer.secho("Finished", fg=typer.colors.GREEN)
        except Exception as exc:
            failures += 1
            typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)

    if failures:
        raise typer.Exit(code=1)


@app.command("langs")
def langs_command(
    url: Annotated[
        str,
        typer.Argument(
            help="YouTube video URL to inspect.",
            metavar="URL",
        ),
    ],
) -> None:
    """Show audio language codes for a URL."""
    langs = core.get_available_audio_langs_for_url(url)
    if not langs:
        typer.secho("No multi-language audio tracks found.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    for lang in sorted(langs):
        typer.echo(lang)
