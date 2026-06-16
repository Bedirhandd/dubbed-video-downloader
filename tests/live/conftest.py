from __future__ import annotations

from pathlib import Path

import pytest
from tests.support import live_helpers
from typer.testing import CliRunner

from dubbed_video_downloader import core, doctor, languages
from dubbed_video_downloader.yt_dlp_types import InfoDict


@pytest.fixture(autouse=True)
def _enable_network_for_live_test() -> None:
    live_helpers.enable_live_network()


@pytest.fixture(scope="session", autouse=True)
def _live_runtime_prerequisites() -> None:
    live_helpers.require_runtime_prerequisites()


@pytest.fixture(scope="session")
def live_test_url() -> str:
    return live_helpers.require_live_test_url()


@pytest.fixture(scope="session")
def live_video_info(live_test_url: str) -> InfoDict:
    info = core.get_video_info(live_test_url)
    formats = info.get("formats")
    assert isinstance(formats, list) and formats, "Expected non-empty format list"
    assert info.get("title"), "Expected video title in metadata"
    return info


@pytest.fixture(scope="session")
def live_language_inventory(live_test_url: str) -> languages.AudioLanguageInventory:
    return core.get_audio_language_inventory_for_url(live_test_url)


@pytest.fixture(scope="session")
def live_test_lang(live_language_inventory: languages.AudioLanguageInventory) -> str:
    return live_helpers.select_live_test_lang(
        live_language_inventory,
        override=live_helpers.optional_live_test_lang_override(),
    )


@pytest.fixture(scope="session")
def live_home(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("live-home")


@pytest.fixture(scope="session")
def live_output_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("live-output")


@pytest.fixture(scope="session")
def live_config_path(
    live_home: Path,
    live_output_dir: Path,
    live_test_lang: str,
) -> Path:
    config_path = live_home / ".config" / "dubbed-video-downloader" / "config.yaml"
    live_helpers.write_live_config(
        config_path,
        live_output_dir,
        default_lang=live_test_lang,
    )
    return config_path


@pytest.fixture(scope="session")
def live_cli_env(live_home: Path) -> dict[str, str]:
    return {"HOME": str(live_home)}


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(scope="session")
def live_doctor_checks(live_config_path: Path) -> list[doctor.CheckResult]:
    return doctor.run_checks(live_config_path)
