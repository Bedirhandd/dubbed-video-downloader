from __future__ import annotations

import errno
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dubbed_video_downloader import core, errors
from tests.conftest import (
    assume_atomic_no_clobber_publish_supported,
    assume_cross_filesystem_temp_roots,
)


def test_finalize_copy_fallback_fail_race_reports_existing_output(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staged_output_path = output_dir / "staging" / "A_Title.mkv"
    staged_output_path.parent.mkdir(parents=True)
    core._write_staging_metadata(staged_output_path.parent)
    staged_output_path.write_text("downloaded media", encoding="utf-8")
    publish_sources: list[Path] = []

    def create_output_before_publish(source_path: Path, destination_path: Path) -> None:
        publish_sources.append(source_path)
        destination_path.write_text("external media", encoding="utf-8")
        raise FileExistsError(errno.EEXIST, "File exists", str(destination_path))

    with (
        patch(
            "dubbed_video_downloader.core.os.link",
            side_effect=OSError("hard links unsupported"),
        ),
        patch(
            "dubbed_video_downloader.core._publish_file_no_clobber",
            side_effect=create_output_before_publish,
        ),
        pytest.raises(errors.DownloadError) as context,
    ):
        core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.FAIL,
        )
    assert "Output already exists" in str(context.value)
    assert output_path.read_text(encoding="utf-8") == "external media"
    assert len(publish_sources) == 1
    assert (
        publish_sources[0].parent == output_path.parent / core.FINALIZING_COPY_DIR_NAME
    )
    assert not publish_sources[0].exists()
    assert staged_output_path.exists()
    assert not (output_path.parent / core.FINALIZING_COPY_DIR_NAME).exists()


def test_finalize_copy_fallback_fails_closed_when_publish_unsupported(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staged_output_path = output_dir / "staging" / "A_Title.mkv"
    staged_output_path.parent.mkdir(parents=True)
    core._write_staging_metadata(staged_output_path.parent)
    staged_output_path.write_text("downloaded media", encoding="utf-8")
    with (
        patch(
            "dubbed_video_downloader.core.os.link",
            side_effect=OSError("hard links unsupported"),
        ),
        patch(
            "dubbed_video_downloader.core._publish_file_no_clobber",
            side_effect=core._AtomicNoClobberPublishUnsupportedError("unsupported"),
        ),
        pytest.raises(errors.DownloadError) as context,
    ):
        core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.SKIP,
        )
    assert "atomic no-clobber publish is unavailable" in str(context.value)
    assert not output_path.exists()
    assert not (output_path.parent / core.FINALIZING_COPY_DIR_NAME).exists()
    assert staged_output_path.exists()


def test_finalize_copy_fallback_removes_partial_output_on_failure(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staged_output_path = output_dir / "staging" / "A_Title.mkv"
    staged_output_path.parent.mkdir(parents=True)
    core._write_staging_metadata(staged_output_path.parent)
    staged_output_path.write_text("downloaded media", encoding="utf-8")

    def fail_after_partial_copy(source, destination, *, length) -> None:
        destination.write(b"partial")
        raise OSError("copy failed")

    with (
        patch(
            "dubbed_video_downloader.core.os.link",
            side_effect=OSError("hard links unsupported"),
        ),
        patch(
            "dubbed_video_downloader.core.shutil.copyfileobj",
            side_effect=fail_after_partial_copy,
        ),
        pytest.raises(errors.DownloadError) as context,
    ):
        core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.SKIP,
        )
    assert "Could not finalize output" in str(context.value)
    assert not output_path.exists()
    assert not (output_path.parent / core.FINALIZING_COPY_DIR_NAME).exists()
    assert staged_output_path.exists()


def test_finalize_copy_fallback_skip_race_preserves_existing_output(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staged_output_path = output_dir / "staging" / "A_Title.mkv"
    staged_output_path.parent.mkdir(parents=True)
    core._write_staging_metadata(staged_output_path.parent)
    staged_output_path.write_text("downloaded media", encoding="utf-8")
    publish_sources: list[Path] = []

    def create_output_before_publish(source_path: Path, destination_path: Path) -> None:
        publish_sources.append(source_path)
        destination_path.write_text("external media", encoding="utf-8")
        raise FileExistsError(errno.EEXIST, "File exists", str(destination_path))

    with (
        patch(
            "dubbed_video_downloader.core.os.link",
            side_effect=OSError("hard links unsupported"),
        ),
        patch(
            "dubbed_video_downloader.core._publish_file_no_clobber",
            side_effect=create_output_before_publish,
        ),
    ):
        status = core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.SKIP,
        )
    assert status == core.DownloadStatus.SKIPPED
    assert output_path.read_text(encoding="utf-8") == "external media"
    assert len(publish_sources) == 1
    assert (
        publish_sources[0].parent == output_path.parent / core.FINALIZING_COPY_DIR_NAME
    )
    assert not publish_sources[0].exists()
    assert staged_output_path.exists()
    assert not (output_path.parent / core.FINALIZING_COPY_DIR_NAME).exists()


def test_finalize_non_overwrite_copies_when_hard_link_fails(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staged_output_path = output_dir / "staging" / "A_Title.mkv"
    staged_output_path.parent.mkdir(parents=True)
    core._write_staging_metadata(staged_output_path.parent)
    staged_output_path.write_text("downloaded media", encoding="utf-8")
    published_sources: list[Path] = []

    def copy_while_final_path_is_absent(source, destination, *, length) -> None:
        destination.write(source.read())
        metadata = json.loads(
            (staged_output_path.parent / core.RUN_METADATA_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        assert (
            str(Path("tr") / "A_Title" / core.FINALIZING_COPY_DIR_NAME)
            in metadata[core.RUN_METADATA_FINALIZING_COPY_DIRS]
        )
        assert not output_path.exists()

    def publish_no_clobber(source_path: Path, destination_path: Path) -> None:
        published_sources.append(source_path)
        source_path.rename(destination_path)

    with (
        patch(
            "dubbed_video_downloader.core.os.link",
            side_effect=OSError("hard links unsupported"),
        ),
        patch(
            "dubbed_video_downloader.core.shutil.copyfileobj",
            side_effect=copy_while_final_path_is_absent,
        ),
        patch(
            "dubbed_video_downloader.core._publish_file_no_clobber",
            side_effect=publish_no_clobber,
        ),
    ):
        status = core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.SKIP,
        )
    assert status == core.DownloadStatus.DOWNLOADED
    assert output_path.read_text(encoding="utf-8") == "downloaded media"
    assert len(published_sources) == 1
    assert (
        published_sources[0].parent
        == output_path.parent / core.FINALIZING_COPY_DIR_NAME
    )
    assert published_sources[0].name == f"{staged_output_path.parent.name}.tmp"
    assert not published_sources[0].exists()
    assert not staged_output_path.exists()
    assert not (output_path.parent / core.FINALIZING_COPY_DIR_NAME).exists()


def test_finalize_non_overwrite_supports_redirected_final_directory(
    tmp_path: Path,
) -> None:
    _output_root, redirected_root = assume_cross_filesystem_temp_roots()
    tmpdir = tmp_path
    with tempfile.TemporaryDirectory(dir=redirected_root) as redirected_tmpdir:
        output_dir = Path(tmpdir)
        redirected_dir = Path(redirected_tmpdir)
        assume_atomic_no_clobber_publish_supported(redirected_dir)
        (output_dir / "tr").symlink_to(redirected_dir, target_is_directory=True)
        output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
        staged_output_path = (
            output_dir
            / "tmp"
            / ".incomplete"
            / "run"
            / "tr"
            / "A_Title"
            / "A_Title.mkv"
        )
        staged_output_path.parent.mkdir(parents=True)
        core._write_staging_metadata(staged_output_path.parent)
        staged_output_path.write_text("downloaded media", encoding="utf-8")
        status = core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.SKIP,
        )
        assert status == core.DownloadStatus.DOWNLOADED
        assert output_path.read_text(encoding="utf-8") == "downloaded media"
        assert not staged_output_path.exists()
        assert not (output_path.parent / core.FINALIZING_COPY_DIR_NAME).exists()


def test_finalize_non_overwrite_uses_hard_link_before_copying(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staged_output_path = output_dir / "staging" / "A_Title.mkv"
    staged_output_path.parent.mkdir(parents=True)
    staged_output_path.write_text("downloaded media", encoding="utf-8")

    def create_final_output(src, dst) -> None:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(Path(src).read_bytes())

    with (
        patch("dubbed_video_downloader.core.os.link") as link,
        patch("dubbed_video_downloader.core.shutil.copyfileobj") as copyfileobj,
    ):
        link.side_effect = create_final_output
        status = core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.SKIP,
        )
    assert status == core.DownloadStatus.DOWNLOADED
    link.assert_called_once_with(staged_output_path, output_path)
    copyfileobj.assert_not_called()
    assert output_path.read_text(encoding="utf-8") == "downloaded media"
    assert not staged_output_path.exists()


def test_finalize_overwrite_copies_when_replace_is_cross_device(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staged_output_path = output_dir / "staging" / "A_Title.mkv"
    staged_output_path.parent.mkdir(parents=True)
    core._write_staging_metadata(staged_output_path.parent)
    staged_output_path.write_text("downloaded media", encoding="utf-8")
    original_replace = Path.replace

    def replace_cross_device_once(path: Path, target: Path) -> Path:
        if path == staged_output_path:
            raise OSError(
                errno.EXDEV, "Invalid cross-device link", str(staged_output_path)
            )
        return original_replace(path, target)

    with patch.object(
        Path, "replace", autospec=True, side_effect=replace_cross_device_once
    ):
        status = core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.OVERWRITE,
        )
    assert status == core.DownloadStatus.DOWNLOADED
    assert output_path.read_text(encoding="utf-8") == "downloaded media"
    assert not staged_output_path.exists()
    assert not (output_path.parent / core.FINALIZING_COPY_DIR_NAME).exists()


def test_finalize_overwrite_replaces_existing_final_output(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staged_output_path = output_dir / "staging" / "A_Title.mkv"
    output_path.parent.mkdir(parents=True)
    staged_output_path.parent.mkdir(parents=True)
    output_path.write_text("external media", encoding="utf-8")
    staged_output_path.write_text("downloaded media", encoding="utf-8")
    status = core._finalize_staged_download(
        staged_output_path=staged_output_path,
        final_output_path=output_path,
        output_dir=output_dir,
        staging_output_dir=staged_output_path.parent,
        exists_behavior=core.FileExistsBehavior.OVERWRITE,
    )
    assert status == core.DownloadStatus.DOWNLOADED
    assert output_path.read_text(encoding="utf-8") == "downloaded media"
    assert not staged_output_path.exists()


def test_finalize_overwrite_supports_redirected_final_directory(tmp_path: Path) -> None:
    _output_root, redirected_root = assume_cross_filesystem_temp_roots()
    tmpdir = tmp_path
    with tempfile.TemporaryDirectory(dir=redirected_root) as redirected_tmpdir:
        output_dir = Path(tmpdir)
        redirected_dir = Path(redirected_tmpdir)
        (output_dir / "tr").symlink_to(redirected_dir, target_is_directory=True)
        output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
        staged_output_path = (
            output_dir
            / "tmp"
            / ".incomplete"
            / "run"
            / "tr"
            / "A_Title"
            / "A_Title.mkv"
        )
        staged_output_path.parent.mkdir(parents=True)
        core._write_staging_metadata(staged_output_path.parent)
        staged_output_path.write_text("downloaded media", encoding="utf-8")
        status = core._finalize_staged_download(
            staged_output_path=staged_output_path,
            final_output_path=output_path,
            output_dir=output_dir,
            staging_output_dir=staged_output_path.parent,
            exists_behavior=core.FileExistsBehavior.OVERWRITE,
        )
        assert status == core.DownloadStatus.DOWNLOADED
        assert output_path.read_text(encoding="utf-8") == "downloaded media"
        assert not staged_output_path.exists()
        assert not (output_path.parent / core.FINALIZING_COPY_DIR_NAME).exists()


def test_no_clobber_publish_maps_posix_errors() -> None:
    with pytest.raises(FileExistsError):
        core._raise_posix_no_clobber_publish_error(
            errno.EEXIST, Path("destination.mkv")
        )
    with pytest.raises(core._AtomicNoClobberPublishUnsupportedError):
        core._raise_posix_no_clobber_publish_error(
            errno.EINVAL, Path("destination.mkv")
        )


def test_no_clobber_publish_maps_windows_errors() -> None:
    with pytest.raises(FileExistsError):
        core._raise_windows_no_clobber_publish_error(
            core.WINDOWS_ERROR_ALREADY_EXISTS, Path("destination.mkv")
        )
    with pytest.raises(core._AtomicNoClobberPublishUnsupportedError):
        core._raise_windows_no_clobber_publish_error(
            core.WINDOWS_ERROR_NOT_SAME_DEVICE, Path("destination.mkv")
        )


def test_publish_file_no_clobber_moves_source_without_overwriting(
    tmp_path: Path,
) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    source_path = output_dir / "source.tmp"
    destination_path = output_dir / "destination.mkv"
    source_path.write_text("downloaded media", encoding="utf-8")
    try:
        core._publish_file_no_clobber(source_path, destination_path)
    except core._AtomicNoClobberPublishUnsupportedError as exc:
        pytest.skip(str(exc))
    assert destination_path.read_text(encoding="utf-8") == "downloaded media"
    assert not source_path.exists()


def test_publish_file_no_clobber_preserves_existing_destination(tmp_path: Path) -> None:
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    source_path = output_dir / "source.tmp"
    destination_path = output_dir / "destination.mkv"
    source_path.write_text("downloaded media", encoding="utf-8")
    destination_path.write_text("external media", encoding="utf-8")
    try:
        with pytest.raises(FileExistsError):
            core._publish_file_no_clobber(source_path, destination_path)
    except core._AtomicNoClobberPublishUnsupportedError as exc:
        pytest.skip(str(exc))
    assert destination_path.read_text(encoding="utf-8") == "external media"
    assert source_path.exists()
