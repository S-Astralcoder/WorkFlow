import argparse
from pathlib import Path

import pytest

from workflow.exceptions import InvalidWorkFlowScript
from workflow.sequence_workflow.construct_workflow import WorkFlowConstructor
from workflow.sequence_workflow.sequence_orchestrator import SequenceOperations


EXAMPLE_DIRECTORY = Path("examples/workflows")


def workflow_args(script_name: str) -> argparse.Namespace:
    return argparse.Namespace(
        workflow_path=str(EXAMPLE_DIRECTORY / script_name),
        workspace=".",
        force=False,
        dry_run=False,
        allow=False,
        show_status=False,
    )


@pytest.mark.parametrize(
    "script_name",
    ["basic_project_setup.toml", "virtual_state_stress_test.toml"],
)
def test_valid_example_workflow_simulates_without_errors(script_name: str) -> None:
    original_directory = Path.cwd()
    workflow_data = WorkFlowConstructor(
        args=workflow_args(script_name)
    ).get_workspace_sequence_data()
    sequence = SequenceOperations(workflow_data=workflow_data)

    sequence.load_workspace_virtual_tree()
    sequence.validate_sequence_operation()

    assert sequence.error_cache == {}
    assert Path.cwd() == original_directory


@pytest.mark.parametrize(
    ("script_name", "expected_action", "expected_message"),
    [
        ("failing_collision.toml", 3, "already exists"),
        ("failing_missing_source.toml", 1, "source path does not exist"),
    ],
)
def test_failing_example_workflow_reports_expected_simulation_error(
    script_name: str, expected_action: int, expected_message: str
) -> None:
    workflow_data = WorkFlowConstructor(
        args=workflow_args(script_name)
    ).get_workspace_sequence_data()
    sequence = SequenceOperations(workflow_data=workflow_data)

    sequence.load_workspace_virtual_tree()
    sequence.validate_sequence_operation()

    assert set(sequence.error_cache) == {expected_action}
    assert expected_message in str(sequence.error_cache[expected_action])


@pytest.mark.parametrize(
    ("script_name", "expected_message"),
    [
        ("invalid_missing_field.toml", "requires non-empty string field 'destination_path'"),
        ("invalid_operation.toml", "unsupported operation 'merge'"),
        ("invalid_toml_syntax.toml", "contains invalid TOML"),
    ],
)
def test_invalid_example_workflow_has_clear_validation_error(
    script_name: str, expected_message: str
) -> None:
    original_directory = Path.cwd()

    with pytest.raises(InvalidWorkFlowScript, match=expected_message):
        WorkFlowConstructor(args=workflow_args(script_name))

    assert Path.cwd() == original_directory
