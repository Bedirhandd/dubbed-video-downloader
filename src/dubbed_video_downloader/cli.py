from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from . import __version__
from . import config as app_config
from . import core
from . import doctor

HELP_EPILOG = """
Examples:

  dbdvdl init

  dbdvdl doctor

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


def _load_config_or_exit() -> app_config.AppConfig:
    try:
        return app_config.load_config()
    except app_config.ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def _normalize_output_dir_or_exit(value: str) -> Path:
    try:
        return app_config.normalize_output_dir(value)
    except app_config.ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def _normalize_ffmpeg_path_or_exit(value: str) -> str:
    try:
        return app_config.normalize_ffmpeg_path(value)
    except app_config.ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def _prompt_value(value: str | None, prompt: str, default: str) -> str:
    if value is not None:
        return value
    if sys.stdin.isatty():
        return str(typer.prompt(prompt, default=default))
    return default


def _write_config_or_exit(output_dir: str, ffmpeg_path: str, force: bool) -> None:
    try:
        path = app_config.write_config(
            output_dir=output_dir,
            ffmpeg_path=ffmpeg_path,
            overwrite=force,
        )
    except app_config.ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Wrote config: {path}", fg=typer.colors.GREEN)


@app.command("init")
def init_command(
    output_dir: Annotated[
        str | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Absolute directory where videos will be saved. Supports ~.",
        ),
    ] = None,
    ffmpeg_path: Annotated[
        str | None,
        typer.Option(
            "--ffmpeg-path",
            help="Path to the FFmpeg executable, or `ffmpeg` to use PATH.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite the existing config file."),
    ] = False,
) -> None:
    """Create the required user config file."""
    selected_output_dir = _prompt_value(
        output_dir,
        "Output directory",
        app_config.DEFAULT_OUTPUT_DIR,
    )
    selected_ffmpeg_path = _prompt_value(
        ffmpeg_path,
        "FFmpeg path",
        app_config.DEFAULT_FFMPEG_PATH,
    )
    _write_config_or_exit(selected_output_dir, selected_ffmpeg_path, force)


@app.command("doctor")
def doctor_command() -> None:
    """Run environment and config checks."""
    results = doctor.run_checks()
    name_width = max(len(result.name) for result in results)

    typer.echo("System check\n")
    for result in results:
        status = "OK" if result.ok else "FAIL"
        color = typer.colors.GREEN if result.ok else typer.colors.RED
        typer.echo(f"{result.name:<{name_width}}  ", nl=False)
        typer.secho(f"{status:<7}", fg=color, nl=False)
        typer.echo(result.detail)

    if not all(result.ok for result in results):
        raise typer.Exit(code=1)

    raise typer.Exit()


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
        str | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Absolute directory where videos will be saved. Supports ~.",
        ),
    ] = None,
    ffmpeg_path: Annotated[
        str | None,
        typer.Option(
            "--ffmpeg-path",
            help="Path to the FFmpeg executable, or `ffmpeg` to use PATH.",
        ),
    ] = None,
) -> None:
    """Download URL(s) with a dub language."""
    loaded_config = _load_config_or_exit()
    effective_output_dir = (
        _normalize_output_dir_or_exit(output_dir)
        if output_dir is not None
        else loaded_config.output_dir
    )
    effective_ffmpeg_path = (
        _normalize_ffmpeg_path_or_exit(ffmpeg_path)
        if ffmpeg_path is not None
        else loaded_config.ffmpeg_path
    )
    ffmpeg_location = app_config.ffmpeg_location_for_yt_dlp(effective_ffmpeg_path)

    failures = 0
    for url in urls:
        typer.echo(f"\n==> Downloading: {url}")
        try:
            core.download(
                url=url,
                lang=lang,
                ffmpeg_path=ffmpeg_location,
                output_dir=effective_output_dir,
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
    _load_config_or_exit()
    langs = core.get_available_audio_langs_for_url(url)
    if not langs:
        typer.secho("No multi-language audio tracks found.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    for lang in sorted(langs):
        typer.echo(lang)
