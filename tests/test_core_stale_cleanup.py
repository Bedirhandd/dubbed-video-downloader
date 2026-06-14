from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from dubbed_video_downloader import core


def test_stale_incomplete_cleanup_does_not_follow_symlinks(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    incomplete_dir = output_dir / "tmp" / ".incomplete"
    outside_dir = Path(tmpdir) / "outside"
    symlink_path = incomplete_dir / "linked"
    outside_dir.mkdir()
    incomplete_dir.mkdir(parents=True)
    (outside_dir / "keep.txt").write_text("keep", encoding="utf-8")
    try:
        symlink_path.symlink_to(outside_dir, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks not supported on this platform")
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert symlink_path.exists()
    assert (outside_dir / "keep.txt").exists()


def test_stale_incomplete_cleanup_handles_redirected_finalizing_parent(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    root_dir = Path(tmpdir)
    output_dir = root_dir / "output"
    redirected_root = root_dir / "redirected"
    redirected_lang_dir = redirected_root / "tr"
    output_dir.mkdir()
    redirected_lang_dir.mkdir(parents=True)
    try:
        (output_dir / "tr").symlink_to(redirected_lang_dir, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks not supported on this platform")
    stale_dir = output_dir / "tmp" / ".incomplete" / "stale-run"
    finalizing_dir = output_dir / "tr" / "A_Title" / core.FINALIZING_COPY_DIR_NAME
    finalizing_copy = finalizing_dir / f"{stale_dir.name}.tmp"
    finalizing_dir.mkdir(parents=True)
    stale_dir.mkdir(parents=True)
    finalizing_copy.write_text("partial", encoding="utf-8")
    core._write_staging_metadata(
        stale_dir,
        finalizing_copy_dirs=(Path("tr") / "A_Title" / core.FINALIZING_COPY_DIR_NAME,),
    )
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert not stale_dir.exists()
    assert not finalizing_copy.exists()
    assert not finalizing_dir.exists()


def test_stale_incomplete_cleanup_ignores_legacy_absolute_finalizing_copy_path(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    stale_dir = output_dir / "tmp" / ".incomplete" / "stale-run"
    outside_dir = output_dir.parent / f"{output_dir.name}-outside-finalizing"
    outside_copy = (
        outside_dir / f"{core.FALLBACK_FINALIZE_COPY_MARKER}.{stale_dir.name}.tmp"
    )
    outside_dir.mkdir()
    stale_dir.mkdir(parents=True)
    outside_copy.write_text("keep", encoding="utf-8")
    (stale_dir / core.RUN_METADATA_FILENAME).write_text(
        json.dumps(
            {
                "application": core.RUN_METADATA_APPLICATION,
                "metadata_version": core.RUN_METADATA_VERSION,
                "finalizing_copy_paths": [str(outside_copy)],
            }
        ),
        encoding="utf-8",
    )
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert not stale_dir.exists()
    assert outside_copy.exists()


def test_stale_incomplete_cleanup_preserves_active_finalizing_copy(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    final_dir = output_dir / "tr" / "A_Title"
    finalizing_dir = final_dir / core.FINALIZING_COPY_DIR_NAME
    active_dir = output_dir / "tmp" / ".incomplete" / "active-run"
    finalizing_copy = finalizing_dir / f"{active_dir.name}.tmp"
    finalizing_dir.mkdir(parents=True)
    active_dir.mkdir(parents=True)
    finalizing_copy.write_text("partial", encoding="utf-8")
    core._write_staging_metadata(
        active_dir,
        finalizing_copy_dirs=(Path("tr") / "A_Title" / core.FINALIZING_COPY_DIR_NAME,),
    )
    active_lock = core._StagingLock(active_dir / core.RUN_LOCK_FILENAME)
    active_lock.acquire(blocking=True)
    try:
        core._cleanup_stale_incomplete_downloads(output_dir)
    finally:
        active_lock.release()
    assert active_dir.exists()
    assert finalizing_copy.exists()


def test_stale_incomplete_cleanup_preserves_invalid_metadata(tmp_path: Path) -> None:
    cases = {
        "malformed": "not json",
        "wrong_app": json.dumps(
            {"application": "other-tool", "metadata_version": core.RUN_METADATA_VERSION}
        ),
        "wrong_version": json.dumps(
            {
                "application": core.RUN_METADATA_APPLICATION,
                "metadata_version": core.RUN_METADATA_VERSION + 1,
            }
        ),
        "legacy": json.dumps({}),
        "non_object": json.dumps([]),
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    incomplete_dir = output_dir / "tmp" / ".incomplete"
    for name, metadata in cases.items():
        candidate_dir = incomplete_dir / name
        candidate_dir.mkdir(parents=True)
        (candidate_dir / core.RUN_METADATA_FILENAME).write_text(
            metadata, encoding="utf-8"
        )
        (candidate_dir / "keep.txt").write_text("keep", encoding="utf-8")
    metadata_dir = incomplete_dir / "metadata_dir"
    metadata_dir.mkdir(parents=True)
    (metadata_dir / core.RUN_METADATA_FILENAME).mkdir()
    (metadata_dir / "keep.txt").write_text("keep", encoding="utf-8")
    core._cleanup_stale_incomplete_downloads(output_dir)
    for name in (*cases, "metadata_dir"):
        candidate_dir = incomplete_dir / name
        assert candidate_dir.exists()
        assert (candidate_dir / "keep.txt").exists()
        assert not (candidate_dir / core.RUN_LOCK_FILENAME).exists()


def test_stale_incomplete_cleanup_preserves_symlinked_metadata(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    candidate_dir = output_dir / "tmp" / ".incomplete" / "linked-metadata"
    target_metadata = output_dir / "metadata.json"
    candidate_dir.mkdir(parents=True)
    target_metadata.write_text(
        json.dumps(
            {
                "application": core.RUN_METADATA_APPLICATION,
                "metadata_version": core.RUN_METADATA_VERSION,
            }
        ),
        encoding="utf-8",
    )
    try:
        (candidate_dir / core.RUN_METADATA_FILENAME).symlink_to(target_metadata)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks not supported on this platform")
    (candidate_dir / "keep.txt").write_text("keep", encoding="utf-8")
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert candidate_dir.exists()
    assert (candidate_dir / "keep.txt").exists()
    assert not (candidate_dir / core.RUN_LOCK_FILENAME).exists()


def test_stale_incomplete_cleanup_preserves_unmatched_finalizing_dirs(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    final_dir = output_dir / "tr" / "A_Title"
    finalizing_dir = final_dir / core.FINALIZING_COPY_DIR_NAME
    stale_dir = output_dir / "tmp" / ".incomplete" / "stale-run"
    outside_dir = output_dir.parent / f"{output_dir.name}-outside-finalizing"
    wrong_run_copy = finalizing_dir / "other-run.tmp"
    non_regular_copy = finalizing_dir / f"{stale_dir.name}.tmp"
    outside_copy = outside_dir / f"{stale_dir.name}.tmp"
    finalizing_dir.mkdir(parents=True)
    outside_dir.mkdir()
    stale_dir.mkdir(parents=True)
    wrong_run_copy.write_text("keep", encoding="utf-8")
    non_regular_copy.mkdir()
    outside_copy.write_text("keep", encoding="utf-8")
    core._write_staging_metadata(
        stale_dir,
        finalizing_copy_dirs=(
            Path("tr") / "A_Title" / core.FINALIZING_COPY_DIR_NAME,
            Path("tr") / "A_Title" / "not-finalizing",
            Path("..") / "outside-finalizing",
            outside_dir,
        ),
    )
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert not stale_dir.exists()
    assert wrong_run_copy.exists()
    assert non_regular_copy.exists()
    assert outside_copy.exists()


def test_stale_incomplete_cleanup_preserves_unowned_directory(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    unowned_dir = output_dir / "tmp" / ".incomplete" / "foreign"
    unowned_dir.mkdir(parents=True)
    (unowned_dir / "keep.txt").write_text("keep", encoding="utf-8")
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert unowned_dir.exists()
    assert (unowned_dir / "keep.txt").exists()
    assert not (unowned_dir / core.RUN_LOCK_FILENAME).exists()


def test_stale_incomplete_cleanup_rejects_symlinked_finalizing_dir(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    root_dir = Path(tmpdir)
    output_dir = root_dir / "output"
    outside_dir = root_dir / "outside-finalizing"
    final_dir = output_dir / "tr" / "A_Title"
    finalizing_dir = final_dir / core.FINALIZING_COPY_DIR_NAME
    stale_dir = output_dir / "tmp" / ".incomplete" / "stale-run"
    output_dir.mkdir()
    outside_dir.mkdir()
    final_dir.mkdir(parents=True)
    try:
        finalizing_dir.symlink_to(outside_dir, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks not supported on this platform")
    outside_copy = outside_dir / f"{stale_dir.name}.tmp"
    stale_dir.mkdir(parents=True)
    outside_copy.write_text("keep", encoding="utf-8")
    core._write_staging_metadata(
        stale_dir,
        finalizing_copy_dirs=(Path("tr") / "A_Title" / core.FINALIZING_COPY_DIR_NAME,),
    )
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert not stale_dir.exists()
    assert finalizing_dir.exists()
    assert outside_copy.exists()


def test_stale_incomplete_cleanup_rejects_symlinked_root(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    incomplete_dir = output_dir / "tmp" / ".incomplete"
    outside_dir = Path(tmpdir) / "outside"
    victim_dir = outside_dir / "victim"
    incomplete_dir.parent.mkdir(parents=True)
    victim_dir.mkdir(parents=True)
    (victim_dir / "keep.txt").write_text("keep", encoding="utf-8")
    try:
        incomplete_dir.symlink_to(outside_dir, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks not supported on this platform")
    with pytest.raises(OSError) as context:
        core._cleanup_stale_incomplete_downloads(output_dir)
    assert "Refusing to use" in str(context.value)
    assert incomplete_dir.exists()
    assert (victim_dir / "keep.txt").exists()


def test_stale_incomplete_cleanup_removes_abandoned_fallback_copy(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    stale_dir = output_dir / "tmp" / ".incomplete" / "stale"
    stale_copy = (
        stale_dir / f"A_Title.mkv{core.FALLBACK_FINALIZE_COPY_MARKER}.abc123.tmp"
    )
    stale_dir.mkdir(parents=True)
    core._write_staging_metadata(stale_dir)
    stale_copy.write_text("partial", encoding="utf-8")
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert not stale_dir.exists()


def test_stale_incomplete_cleanup_removes_recorded_finalizing_copy(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    final_dir = output_dir / "tr" / "A_Title"
    finalizing_dir = final_dir / core.FINALIZING_COPY_DIR_NAME
    stale_dir = output_dir / "tmp" / ".incomplete" / "stale-run"
    finalizing_copy = finalizing_dir / f"{stale_dir.name}.tmp"
    finalizing_dir.mkdir(parents=True)
    stale_dir.mkdir(parents=True)
    finalizing_copy.write_text("partial", encoding="utf-8")
    core._write_staging_metadata(
        stale_dir,
        finalizing_copy_dirs=(Path("tr") / "A_Title" / core.FINALIZING_COPY_DIR_NAME,),
    )
    core._cleanup_stale_incomplete_downloads(output_dir)
    assert not stale_dir.exists()
    assert not finalizing_copy.exists()
    assert not finalizing_dir.exists()


def test_stale_incomplete_cleanup_removes_unlocked_runs_only(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    incomplete_dir = output_dir / "tmp" / ".incomplete"
    stale_dir = incomplete_dir / "stale"
    active_dir = incomplete_dir / "active"
    stale_dir.mkdir(parents=True)
    active_dir.mkdir(parents=True)
    core._write_staging_metadata(stale_dir)
    core._write_staging_metadata(active_dir)
    (stale_dir / "partial.part").write_text("stale", encoding="utf-8")
    (active_dir / "partial.part").write_text("active", encoding="utf-8")
    active_lock = core._StagingLock(active_dir / core.RUN_LOCK_FILENAME)
    active_lock.acquire(blocking=True)
    try:
        core._cleanup_stale_incomplete_downloads(output_dir)
    finally:
        active_lock.release()
    assert not stale_dir.exists()
    assert active_dir.exists()


def test_stale_incomplete_cleanup_retries_finalizing_copy_delete_failure(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    final_dir = output_dir / "tr" / "A_Title"
    finalizing_dir = final_dir / core.FINALIZING_COPY_DIR_NAME
    stale_dir = output_dir / "tmp" / ".incomplete" / "stale-run"
    finalizing_copy = finalizing_dir / f"{stale_dir.name}.tmp"
    finalizing_dir.mkdir(parents=True)
    stale_dir.mkdir(parents=True)
    finalizing_copy.write_text("partial", encoding="utf-8")
    core._write_staging_metadata(
        stale_dir,
        finalizing_copy_dirs=(Path("tr") / "A_Title" / core.FINALIZING_COPY_DIR_NAME,),
    )
    original_unlink = core.os.unlink

    def fail_finalizing_copy_unlink(path, *args, **kwargs) -> None:
        if (path == finalizing_copy.name and kwargs.get("dir_fd") is not None) or Path(
            path
        ) == finalizing_copy:
            raise OSError("cannot delete finalizing copy")
        return original_unlink(path, *args, **kwargs)

    with patch(
        "dubbed_video_downloader.core.os.unlink",
        side_effect=fail_finalizing_copy_unlink,
    ):
        core._cleanup_stale_incomplete_downloads(output_dir)
    assert stale_dir.exists()
    assert finalizing_copy.exists()
