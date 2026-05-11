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

  dbdvdl config show

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

config_app = typer.Typer(
    help="Manage the required user config.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
app.add_typer(config_app, name="config")


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
    if _stdin_is_interactive():
        return str(typer.prompt(prompt, default=default))
    return default


def _stdin_is_interactive() -> bool:
    return sys.stdin.isatty()


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


def _init_config(output_dir: str | None, ffmpeg_path: str | None, force: bool) -> None:
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


def _print_config_recreate_hint() -> None:
    typer.echo("\nYou can create a new config with:")
    typer.echo("  dbdvdl init")
    typer.echo("  dbdvdl init --output-dir ~/Videos --ffmpeg-path /path/to/ffmpeg")


def _print_label_value(label: str, value: object) -> None:
    typer.secho(f"{label}: ", fg=typer.colors.CYAN, bold=True, nl=False)
    typer.echo(value)


def _print_command_header(action: str, url: str) -> None:
    typer.echo()
    typer.secho("==> ", fg=typer.colors.CYAN, bold=True, nl=False)
    typer.secho(action, fg=typer.colors.CYAN, bold=True, nl=False)
    typer.echo(f": {url}")


def _print_download_plan(plan: core.DownloadPlan) -> None:
    typer.secho("Dry run", fg=typer.colors.YELLOW, bold=True, nl=False)
    typer.echo(": no files will be downloaded or created.")
    if plan.title:
        _print_label_value("Title", plan.title)
    if plan.uploader:
        _print_label_value("Channel", plan.uploader)
    _print_label_value("Language", plan.lang)
    if plan.available_langs:
        _print_label_value("Available languages", ", ".join(plan.available_langs))
    _print_label_value("Output", plan.output_path)


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
    _init_config(output_dir, ffmpeg_path, force)


@config_app.command("init")
def config_init_command(
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
    _init_config(output_dir, ffmpeg_path, force)


@config_app.command("show")
def config_show_command() -> None:
    """Show the resolved user config."""
    loaded_config = _load_config_or_exit()
    typer.echo(f"Config path: {app_config.get_config_path()}")
    typer.echo(f"Output directory: {loaded_config.output_dir}")
    typer.echo(f"FFmpeg path: {loaded_config.ffmpeg_path}")


@config_app.command("remove")
def config_remove_command(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Remove config without confirmation."),
    ] = False,
) -> None:
    """Remove the user config directory."""
    config_dir = app_config.get_config_dir()
    if not config_dir.exists():
        typer.echo(f"No config found at {config_dir}.")
        typer.echo("Nothing to remove.")
        return

    if not yes:
        if not _stdin_is_interactive():
            typer.secho(
                "Refusing to remove config non-interactively without --yes.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

        confirmed = typer.confirm(f"Remove config directory {config_dir}?")
        if not confirmed:
            typer.echo("Config removal cancelled.")
            return

    try:
        removed_path = app_config.remove_config_dir(config_dir)
    except app_config.ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    if removed_path is None:
        typer.echo(f"No config found at {config_dir}.")
        typer.echo("Nothing to remove.")
        return

    typer.secho(f"Removed config directory: {removed_path}", fg=typer.colors.GREEN)
    _print_config_recreate_hint()


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
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Validate metadata and print the planned output without downloading.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show yt-dlp warnings and debug output.",
        ),
    ] = False,
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
        action = "Dry run" if dry_run else "Downloading"
        _print_command_header(action, url)
        try:
            if dry_run:
                plan = core.plan_download(
                    url=url,
                    lang=lang,
                    ffmpeg_path=ffmpeg_location,
                    output_dir=effective_output_dir,
                    verbose=verbose,
                )
                _print_download_plan(plan)
                typer.secho("Dry run OK", fg=typer.colors.GREEN, bold=True)
            else:
                core.download(
                    url=url,
                    lang=lang,
                    ffmpeg_path=ffmpeg_location,
                    output_dir=effective_output_dir,
                    verbose=verbose,
                )
                typer.secho("Finished", fg=typer.colors.GREEN, bold=True)
        except Exception as exc:
            failures += 1
            typer.secho(f"Error: {exc}", fg=typer.colors.RED, bold=True, err=True)

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
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show yt-dlp warnings and debug output.",
        ),
    ] = False,
) -> None:
    """Show audio language codes for a URL."""
    _load_config_or_exit()
    langs = core.get_available_audio_langs_for_url(url, verbose=verbose)
    if not langs:
        typer.secho("No multi-language audio tracks found.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    for lang in sorted(langs):
        typer.echo(lang)
