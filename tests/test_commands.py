from pathlib import Path

import pytest

from pathflow.command_line import CommandLine
from pathflow.exceptions import (
    CollisionError,
    FileAlreadyExists,
    InvalidFileName,
    InvalidFileType,
    InvalidItemType,
    InvalidSelfMove,
    OutOfScope,
    SameFileError,
    WorkspacePathInvalid,
    WorkspaceProtection,
)
from pathflow.operations import (
    CopyCommand,
    CreateCommand,
    DeleteCommand,
    MoveCommand,
    RenameCommand,
)
from pathflow.operations.response import Status


def parse_args(workspace: Path, *operation_args: str, flags: tuple[str, ...] = ()):
    return CommandLine().get_parser(
        ["--workspace", str(workspace), *flags, *operation_args]
    )


def test_non_existing_workspace(tmp_path: Path) -> None:
    invalid_workspace = tmp_path / "test" / "myspace"
    target = invalid_workspace / "my"

    with pytest.raises(WorkspacePathInvalid):
        CreateCommand(parse_args(invalid_workspace, "create", "file", str(target)))


def test_out_of_scope(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(OutOfScope):
        DeleteCommand(parse_args(workspace, "delete", str(tmp_path)))


def test_workspace_protection(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceProtection):
        DeleteCommand(parse_args(tmp_path, "delete", str(tmp_path)))


def test_create_rejects_existing_target_without_force(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("keep me", encoding="utf-8")

    with pytest.raises(FileAlreadyExists):
        CreateCommand(parse_args(tmp_path, "create", "file", str(target)))


def test_force_create_does_not_truncate_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("keep me", encoding="utf-8")
    command = CreateCommand(
        parse_args(tmp_path, "create", "file", str(target), flags=("--force",))
    )

    result = command.execute_command()

    assert result.status is Status.SUCCESSFUL
    assert target.read_text(encoding="utf-8") == "keep me"


def test_create_dry_run_leaves_existing_target_unchanged(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("original", encoding="utf-8")
    command = CreateCommand(
        parse_args(
            tmp_path,
            "create",
            "file",
            str(target),
            flags=("--force", "--dry-run"),
        )
    )

    result = command.execute_command()

    assert result.status is Status.DRY_RUN
    assert target.read_text(encoding="utf-8") == "original"


def test_copy_rejects_file_as_destination(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination.txt"
    source.touch()
    destination.touch()

    with pytest.raises(InvalidItemType):
        CopyCommand(parse_args(tmp_path, "copy", str(source), str(destination)))


def test_copy_detects_name_collision_before_execution(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination"
    source.write_text("new", encoding="utf-8")
    destination.mkdir()
    (destination / source.name).write_text("old", encoding="utf-8")

    with pytest.raises(CollisionError):
        CopyCommand(parse_args(tmp_path, "copy", str(source), str(destination)))


def test_force_copy_overwrites_colliding_file(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination"
    source.write_text("new", encoding="utf-8")
    destination.mkdir()
    copied_file = destination / source.name
    copied_file.write_text("old", encoding="utf-8")
    command = CopyCommand(
        parse_args(
            tmp_path,
            "copy",
            str(source),
            str(destination),
            flags=("--force",),
        )
    )

    result = command.execute_command()

    assert result.status is Status.SUCCESSFUL
    assert copied_file.read_text(encoding="utf-8") == "new"


@pytest.mark.parametrize("force", [False, True])
def test_copy_directory_to_itself_is_always_rejected(
    tmp_path: Path, force: bool
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    flags = ("--force",) if force else ()

    with pytest.raises(SameFileError):
        CopyCommand(
            parse_args(tmp_path, "copy", str(source), str(source), flags=flags)
        )


def test_copy_dry_run_does_not_create_destination_item(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination"
    source.touch()
    destination.mkdir()
    command = CopyCommand(
        parse_args(
            tmp_path,
            "copy",
            str(source),
            str(destination),
            flags=("--dry-run",),
        )
    )

    result = command.execute_command()

    assert result.status is Status.DRY_RUN
    assert not (destination / source.name).exists()


def test_copy_reports_unexpected_execution_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination"
    source.touch()
    destination.mkdir()
    command = CopyCommand(parse_args(tmp_path, "copy", str(source), str(destination)))

    def fail_copy(*_args: object, **_kwargs: object) -> None:
        raise OSError("copy blocked")

    monkeypatch.setattr("pathflow.operations.copy.shutil.copy2", fail_copy)
    result = command.execute_command()

    assert result.status is Status.FAILED
    assert result.error == "copy blocked"


@pytest.mark.parametrize("force", [False, True])
def test_move_directory_into_descendant_is_always_rejected(
    tmp_path: Path, force: bool
) -> None:
    source = tmp_path / "source"
    descendant = source / "descendant"
    descendant.mkdir(parents=True)
    flags = ("--force",) if force else ()

    with pytest.raises(InvalidSelfMove):
        MoveCommand(
            parse_args(tmp_path, "move", str(source), str(descendant), flags=flags)
        )


def test_move_dry_run_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination"
    source.touch()
    destination.mkdir()
    command = MoveCommand(
        parse_args(
            tmp_path,
            "move",
            str(source),
            str(destination),
            flags=("--dry-run",),
        )
    )

    result = command.execute_command()

    assert result.status is Status.DRY_RUN
    assert source.exists()
    assert not (destination / source.name).exists()


def test_move_reports_unexpected_execution_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination"
    source.touch()
    destination.mkdir()
    command = MoveCommand(parse_args(tmp_path, "move", str(source), str(destination)))

    def fail_move(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("move blocked")

    monkeypatch.setattr("pathflow.operations.move.shutil.move", fail_move)
    result = command.execute_command()

    assert result.status is Status.FAILED
    assert result.error == "move blocked"


@pytest.mark.parametrize("new_name", ["nested/name.txt", "nested\\name.txt", "bad:name.txt"])
def test_rename_rejects_names_containing_path_or_invalid_characters(
    tmp_path: Path, new_name: str
) -> None:
    source = tmp_path / "source.txt"
    source.touch()

    with pytest.raises(InvalidFileName):
        RenameCommand(parse_args(tmp_path, "rename", str(source), new_name))


def test_rename_rejects_extension_change_without_force(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.touch()

    with pytest.raises(InvalidFileType):
        RenameCommand(parse_args(tmp_path, "rename", str(source), "source.md"))


def test_force_rename_allows_extension_change(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("content", encoding="utf-8")
    renamed = tmp_path / "source.md"
    command = RenameCommand(
        parse_args(
            tmp_path,
            "rename",
            str(source),
            renamed.name,
            flags=("--force",),
        )
    )

    result = command.execute_command()

    assert result.status is Status.SUCCESSFUL
    assert not source.exists()
    assert renamed.read_text(encoding="utf-8") == "content"


def test_rename_dry_run_preserves_original_name(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.touch()
    renamed = tmp_path / "renamed.txt"
    command = RenameCommand(
        parse_args(
            tmp_path,
            "rename",
            str(source),
            renamed.name,
            flags=("--dry-run",),
        )
    )

    result = command.execute_command()

    assert result.status is Status.DRY_RUN
    assert source.exists()
    assert not renamed.exists()


def test_rename_reports_unexpected_execution_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.txt"
    source.touch()
    command = RenameCommand(
        parse_args(tmp_path, "rename", str(source), "renamed.txt")
    )

    def fail_rename(_self: Path, _target: Path) -> Path:
        raise PermissionError("rename blocked")

    monkeypatch.setattr(Path, "rename", fail_rename)
    result = command.execute_command()

    assert result.status is Status.FAILED
    assert result.error == "rename blocked"


def test_delete_denied_by_user_is_skipped(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.touch()
    command = DeleteCommand(parse_args(tmp_path, "delete", str(target)))

    result = command.execute_command(lambda _prompt: False)

    assert result.status is Status.SKIPPED
    assert target.exists()


def test_delete_allow_flag_bypasses_permission_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.txt"
    target.touch()
    command = DeleteCommand(
        parse_args(
            tmp_path,
            "delete",
            str(target),
            flags=("--allow", "--force"),
        )
    )

    def unexpected_prompt(_prompt: str) -> bool:
        pytest.fail("permission callback must not run with --allow")

    removed: list[Path] = []

    def record_remove(path: Path) -> None:
        removed.append(path)

    monkeypatch.setattr("pathflow.operations.delete.os.remove", record_remove)
    result = command.execute_command(unexpected_prompt)

    assert result.status is Status.SUCCESSFUL
    assert removed == [target]


def test_delete_dry_run_never_requests_permission(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.touch()
    command = DeleteCommand(
        parse_args(tmp_path, "delete", str(target), flags=("--dry-run",))
    )

    def unexpected_prompt(_prompt: str) -> bool:
        pytest.fail("dry-run must not request permission")

    result = command.execute_command(unexpected_prompt)

    assert result.status is Status.DRY_RUN
    assert target.exists()


def test_non_force_delete_uses_recycle_bin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.txt"
    target.touch()
    command = DeleteCommand(
        parse_args(tmp_path, "delete", str(target), flags=("--allow",))
    )
    trashed: list[Path] = []

    def record_trashed(path: Path) -> None:
        trashed.append(path)

    monkeypatch.setattr(
        "pathflow.operations.delete.send2trash.send2trash",
        record_trashed,
    )

    result = command.execute_command(lambda _prompt: False)

    assert result.status is Status.SUCCESSFUL
    assert trashed == [target]


@pytest.mark.parametrize("exception_type", [OSError, PermissionError])
def test_delete_reports_filesystem_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[OSError],
) -> None:
    target = tmp_path / "target.txt"
    target.touch()
    command = DeleteCommand(
        parse_args(
            tmp_path,
            "delete",
            str(target),
            flags=("--allow", "--force"),
        )
    )

    def fail_remove(_path: Path) -> None:
        raise exception_type("delete blocked")

    monkeypatch.setattr("pathflow.operations.delete.os.remove", fail_remove)
    result = command.execute_command(_unused_permission)

    assert result.status is Status.FAILED
    assert result.error == "delete blocked"


def _unused_permission(_prompt: str) -> bool:
    return False
