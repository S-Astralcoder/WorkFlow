from pathlib import Path
from typing import Any

from workflow.sequence_workflow.sequence_orchestrator import SequenceOperations


def workflow_data(workspace: Path, actions: list[dict[str, Any]], force: bool = False) -> dict[str, Any]:
    return {
        "meta-data": {
            "workspace": str(workspace),
            "force": force,
            "dry_run": False,
            "allow": False,
            "show_status": False,
        },
        "actions": actions,
    }


def test_sequence_operations_update_virtual_tree_in_order(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    destination = tmp_path / "destination"
    destination.mkdir()
    container = tmp_path / "container"

    actions: list[dict[str, Any]] = [
        {"id": 1, "operation": "create", "type": "folder", "path": container, "recursive": False},
        {"id": 2, "operation": "copy", "source_path": source, "destination_path": container},
        {"id": 3, "operation": "move", "source_path": container / source.name, "destination_path": destination},
        {"id": 4, "operation": "rename", "path": destination / source.name, "new_name": "renamed.txt"},
        {"id": 5, "operation": "delete", "path": source},
    ]
    sequence = SequenceOperations(workflow_data=workflow_data(tmp_path, actions))
    sequence.load_workspace_virtual_tree()

    sequence.validate_sequence_operation()

    assert sequence.error_cache == {}
    assert sequence.virtual_tree.path_exists_and_type(("container",), "folder")
    assert not sequence.virtual_tree.path_exists(("container", "source.txt"))
    assert sequence.virtual_tree.path_exists_and_type(("destination", "renamed.txt"), "file")
    assert not sequence.virtual_tree.path_exists(("source.txt",))


def test_sequence_errors_are_cached_by_action_and_simulation_continues(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    outside_path = tmp_path.parent / "outside.txt"
    valid_path = tmp_path / "created-after-errors"

    actions: list[dict[str, Any]] = [
        {"id": 1, "operation": "create", "type": "file", "path": outside_path, "recursive": False},
        {"id": 2, "operation": "copy", "source_path": tmp_path / "missing.txt", "destination_path": tmp_path},
        {"id": 3, "operation": "move", "source_path": source, "destination_path": tmp_path / "missing-folder"},
        {"id": 4, "operation": "rename", "path": tmp_path / "missing.txt", "new_name": "renamed.txt"},
        {"id": 5, "operation": "delete", "path": tmp_path / "missing.txt"},
        {"id": 6, "operation": "unsupported"},
        {"id": 7, "operation": "delete", "path": tmp_path},
        {"id": 8, "operation": "create", "type": "folder", "path": valid_path, "recursive": False},
    ]
    sequence = SequenceOperations(workflow_data=workflow_data(tmp_path, actions))
    sequence.load_workspace_virtual_tree()

    sequence.validate_sequence_operation()

    assert set(sequence.error_cache) == {1, 2, 3, 4, 5, 6, 7}
    assert "Action 1 ('create') would fail" in str(sequence.error_cache[1])
    assert "outside workspace" in str(sequence.error_cache[1])
    assert "Action 2 ('copy') would fail" in str(sequence.error_cache[2])
    assert "source path does not exist" in str(sequence.error_cache[2])
    assert "Action 3 ('move') would fail" in str(sequence.error_cache[3])
    assert "destination path does not exist" in str(sequence.error_cache[3])
    assert "Action 4 ('rename') would fail" in str(sequence.error_cache[4])
    assert "Action 5 ('delete') would fail" in str(sequence.error_cache[5])
    assert "unsupported operation" in str(sequence.error_cache[6])
    assert "Action 7 ('delete') would fail" in str(sequence.error_cache[7])
    assert "workspace root" in str(sequence.error_cache[7])
    assert sequence.virtual_tree.path_exists_and_type(("created-after-errors",), "folder")
