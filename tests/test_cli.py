from argparse import Namespace
from typing import ClassVar

import pytest

import workflow as workflow_package
from workflow import cli
from workflow.operations.response import CommandResult, Status


class StubCommand:
    instances: ClassVar[list["StubCommand"]] = []
    result: ClassVar[CommandResult] = CommandResult(
        status=Status.SUCCESSFUL,
        message="command result",
    )

    def __init__(self, args: Namespace) -> None:
        self.args = args
        self.execute_args: tuple[object, ...] = ()
        self.execute_kwargs: dict[str, object] = {}
        self.instances.append(self)

    def execute_command(self, *args: object, **kwargs: object) -> CommandResult:
        self.execute_args = args
        self.execute_kwargs = kwargs
        return self.result


@pytest.fixture(autouse=True)
def clear_stub_instances() -> None:
    StubCommand.instances.clear()


def parser_result(
    operation: str, *, dry_run: bool = False, show_status: bool = False
) -> Namespace:
    return Namespace(
        operation=operation,
        dry_run=dry_run,
        show_status=show_status,
    )


def stub_parser(
    monkeypatch: pytest.MonkeyPatch, result: Namespace
) -> list[list[str] | None]:
    received_args: list[list[str] | None] = []

    def get_parser(_self: object, args: list[str] | None = None) -> Namespace:
        received_args.append(args)
        return result

    monkeypatch.setattr(cli.CommandLine, "get_parser", get_parser)
    return received_args


@pytest.mark.parametrize(
    ("operation", "command_name"),
    [
        ("create", "CreateCommand"),
        ("copy", "CopyCommand"),
        ("move", "MoveCommand"),
        ("rename", "RenameCommand"),
    ],
)
def test_workflow_dispatches_non_delete_operations(
    operation: str,
    command_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed_args = parser_result(operation)
    received_args = stub_parser(monkeypatch, parsed_args)
    monkeypatch.setattr(cli, command_name, StubCommand)
    raw_args = [operation, "example"]

    exit_code = cli.workflow(raw_args)

    assert exit_code == 0
    assert received_args == [raw_args]
    assert len(StubCommand.instances) == 1
    command = StubCommand.instances[0]
    assert command.args is parsed_args
    assert command.execute_args == ()
    assert command.execute_kwargs == {}


def test_workflow_passes_permission_callback_to_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed_args = parser_result("delete")
    stub_parser(monkeypatch, parsed_args)
    monkeypatch.setattr(cli, "DeleteCommand", StubCommand)

    cli.workflow(["delete", "example"])

    command = StubCommand.instances[0]
    assert command.args is parsed_args
    assert command.execute_args == ()
    assert command.execute_kwargs == {"permission_func": cli.permission_func}


@pytest.mark.parametrize(
    ("dry_run", "show_status", "should_display"),
    [
        (False, False, False),
        (True, False, True),
        (False, True, True),
        (True, True, True),
    ],
)
def test_workflow_displays_results_only_when_requested(
    dry_run: bool,
    show_status: bool,
    should_display: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    stub_parser(
        monkeypatch,
        parser_result("create", dry_run=dry_run, show_status=show_status),
    )
    monkeypatch.setattr(cli, "CreateCommand", StubCommand)

    cli.workflow([])

    assert (StubCommand.result.message in capsys.readouterr().out) is should_display


def test_workflow_always_displays_failed_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    stub_parser(monkeypatch, parser_result("create"))
    monkeypatch.setattr(cli, "CreateCommand", StubCommand)
    monkeypatch.setattr(
        StubCommand,
        "result",
        CommandResult(
            status=Status.FAILED,
            message="Failed to create item.",
            error="creation blocked",
        ),
    )

    exit_code = cli.workflow([])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Failed to create item." in output
    assert "creation blocked" in output


def test_main_exits_with_workflow_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failed_workflow() -> int:
        return 1

    monkeypatch.setattr(workflow_package, "workflow", failed_workflow)

    with pytest.raises(SystemExit) as error:
        workflow_package.main()

    assert error.value.code == 1


@pytest.mark.parametrize(
    ("response", "expected"),
    [("yes", True), ("no", False)],
)
def test_permission_func_converts_prompt_response_to_boolean(
    response: str,
    expected: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt_calls: list[dict[str, object]] = []

    def ask(**kwargs: object) -> str:
        prompt_calls.append(kwargs)
        return response

    monkeypatch.setattr(cli.Prompt, "ask", ask)

    assert cli.permission_func("Continue?") is expected
    assert prompt_calls == [
        {
            "prompt": "Continue?",
            "choices": ["yes", "no"],
            "case_sensitive": False,
            "default": "no",
        }
    ]


def test_workflow_reports_an_invalid_operation_from_parser(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    stub_parser(monkeypatch, parser_result("unexpected"))

    exit_code = cli.workflow([])

    assert exit_code == 1
    assert "Invalid Operator" in capsys.readouterr().out


def test_workflow_accepts_no_explicit_argument_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received_args = stub_parser(monkeypatch, parser_result("unexpected"))

    cli.workflow()

    assert received_args == [None]
