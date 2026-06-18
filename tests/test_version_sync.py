from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import tomllib
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
WORKFLOW_PATHS = (
    REPO_ROOT / ".github" / "workflows" / "ci.yml",
    REPO_ROOT / ".github" / "workflows" / "release.yml",
)
EXPECTED_SETUP_UV_VERSION = "0.11.7"

CURATED_VERSION_PATTERNS: dict[Path, str] = {
    REPO_ROOT / "src" / "dubbed_video_downloader" / "__init__.py": (
        r'^__version__ = "([^"]+)"$'
    ),
    REPO_ROOT / "docs" / "index.md": r"^\*\*Version:\*\* ([0-9]+\.[0-9]+\.[0-9]+)$",
    REPO_ROOT / "docs" / "commands" / "overview.md": (
        r"^dbdvdl ([0-9]+\.[0-9]+\.[0-9]+)$"
    ),
    REPO_ROOT / "docs" / "architecture" / "overview.md": r'__version__ = "([^"]+)"',
}
EXACT_PIN_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?==[^\s;]+$")


def _load_pyproject() -> dict[str, Any]:
    return tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))


def _pyproject_version() -> str:
    version = _load_pyproject()["project"]["version"]
    assert isinstance(version, str)
    return version


def _extract_single_version_match(path: Path, pattern: str) -> str:
    matches = re.findall(pattern, path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    assert matches, (
        f"Could not find a version declaration in {path.relative_to(REPO_ROOT)}"
    )
    assert len(matches) == 1, (
        f"Expected exactly one version declaration in {path.relative_to(REPO_ROOT)}, "
        f"found {len(matches)}"
    )
    match = matches[0]
    assert isinstance(match, str)
    return match


def test_release_version_is_synced_across_metadata_and_curated_docs() -> None:
    expected_version = _pyproject_version()

    for path, pattern in CURATED_VERSION_PATTERNS.items():
        observed_version = _extract_single_version_match(path, pattern)
        assert observed_version == expected_version, (
            f"{path.relative_to(REPO_ROOT)} declares {observed_version}, "
            f"expected {expected_version}"
        )


def test_direct_dependencies_are_exact_pins() -> None:
    pyproject = _load_pyproject()
    requirement_groups = {
        "[project].dependencies": pyproject["project"]["dependencies"],
        "[build-system].requires": pyproject["build-system"]["requires"],
        "[dependency-groups].dev": pyproject["dependency-groups"]["dev"],
    }

    for group_name, requirements in requirement_groups.items():
        assert isinstance(requirements, list)
        for requirement in requirements:
            assert isinstance(requirement, str)
            assert EXACT_PIN_PATTERN.fullmatch(requirement), (
                f"{group_name} must use exact pins, found {requirement!r}"
            )


def test_workflows_use_one_exact_setup_uv_version() -> None:
    for workflow_path in WORKFLOW_PATHS:
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        assert isinstance(workflow, dict)
        jobs = workflow.get("jobs")
        assert isinstance(jobs, dict)

        matched_steps = 0
        for job in jobs.values():
            assert isinstance(job, dict)
            steps = job.get("steps")
            assert isinstance(steps, list)

            for step in steps:
                assert isinstance(step, dict)
                uses = step.get("uses")
                if not isinstance(uses, str) or not uses.startswith(
                    "astral-sh/setup-uv@"
                ):
                    continue

                matched_steps += 1
                with_config = step.get("with")
                assert isinstance(with_config, dict)
                observed_version = with_config.get("version")
                assert observed_version == EXPECTED_SETUP_UV_VERSION, (
                    f"{workflow_path.relative_to(REPO_ROOT)} must pin setup-uv to "
                    f"{EXPECTED_SETUP_UV_VERSION}, found {observed_version!r}"
                )

        assert matched_steps > 0, (
            f"Expected at least one setup-uv step in "
            f"{workflow_path.relative_to(REPO_ROOT)}"
        )
