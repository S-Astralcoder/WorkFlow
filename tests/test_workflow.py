import argparse
from pathlib import Path
from typing import Any

from workflow.command_line import CommandLine
from workflow.sequence_workflow.workflow import ExecuteWorkflow


def test_constructs_every_operation_with_allow_and_matching_paths(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace with spaces"
    workspace.mkdir()

    create_path = workspace / "created file.txt"
    source_path = workspace / "source file.txt"
    destination_path = workspace / "destination folder"
    renamed_source = destination_path / source_path.name

    workflow_data: dict[str, Any] = {
        "meta-data": {
            "workspace": workspace,
            "force": True,
            "dry_run": True,
            "allow": False,
            "show_status": True,
        },
        "actions": [
            {"id": 1, "operation": "create", "type": "file", "path": create_path, "recursive": True},
            {"id": 2, "operation": "copy", "source_path": source_path, "destination_path": destination_path},
            {"id": 3, "operation": "move", "source_path": source_path, "destination_path": destination_path},
            {"id": 4, "operation": "rename", "path": renamed_source, "new_name": "renamed file.txt"},
            {"id": 5, "operation": "delete", "path": create_path},
        ],
    }
    executor = ExecuteWorkflow(workflow_data=workflow_data, args=argparse.Namespace())

    executor.construct_command()
    executor.construct_command()

    assert executor.allow is True
    assert len(executor.sequence_execution_commands) == 5

    parsed_commands = [CommandLine().get_parser(command) for command in executor.sequence_execution_commands]
    for parsed in parsed_commands:
        assert parsed.allow is True
        assert parsed.force is True
        assert parsed.dry_run is True
        assert parsed.show_status is True
        assert Path(parsed.workspace) == workspace.resolve()

    create, copy, move, rename, delete = parsed_commands
    assert create.operation == "create"
    assert create.recursive is True
    assert Path(create.path) == create_path

    assert copy.operation == "copy"
    assert Path(copy.source_path) == source_path
    assert Path(copy.destination_path) == destination_path

    assert move.operation == "move"
    assert Path(move.source_path) == source_path
    assert Path(move.destination_path) == destination_path

    assert rename.operation == "rename"
    assert Path(rename.path) == renamed_source
    assert rename.new_name == "renamed file.txt"

    assert delete.operation == "delete"
    assert Path(delete.path) == create_path


def test_relative_action_path_is_anchored_to_workspace(tmp_path: Path) -> None:
    workflow_data: dict[str, Any] = {
        "meta-data": {
            "workspace": tmp_path,
            "force": False,
            "dry_run": False,
            "allow": False,
            "show_status": False,
        },
        "actions": [
            {"id": 1, "operation": "delete", "path": Path("nested") / "item.txt"},
        ],
    }
    executor = ExecuteWorkflow(workflow_data=workflow_data, args=argparse.Namespace())

    executor.construct_command()

    parsed = CommandLine().get_parser(executor.sequence_execution_commands[0])
    assert parsed.allow is True
    assert Path(parsed.path) == tmp_path.resolve() / "nested" / "item.txt"
