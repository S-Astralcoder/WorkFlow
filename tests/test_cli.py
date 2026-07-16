from argparse import Namespace
from typing import ClassVar

import pytest

from pathflow import cli


class StubCommand:
    instances: ClassVar[list["StubCommand"]] = []
    result: ClassVar[str] = "command result"

    def __init__(self, args: Namespace) -> None:
        self.args = args
        self.execute_args: tuple[object, ...] = ()
        self.execute_kwargs: dict[str, object] = {}
        self.instances.append(self)

    def execute_command(self, *args: object, **kwargs: object) -> str:
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
def test_pathflow_dispatches_non_delete_operations(
    operation: str,
    command_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed_args = parser_result(operation)
    received_args = stub_parser(monkeypatch, parsed_args)
    monkeypatch.setattr(cli, command_name, StubCommand)
    raw_args = [operation, "example"]

    cli.pathflow(raw_args)

    assert received_args == [raw_args]
    assert len(StubCommand.instances) == 1
    command = StubCommand.instances[0]
    assert command.args is parsed_args
    assert command.execute_args == ()
    assert command.execute_kwargs == {}


def test_pathflow_passes_permission_callback_to_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed_args = parser_result("delete")
    stub_parser(monkeypatch, parsed_args)
    monkeypatch.setattr(cli, "DeleteCommand", StubCommand)

    cli.pathflow(["delete", "example"])

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
def test_pathflow_displays_results_only_when_requested(
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

    cli.pathflow([])

    assert (StubCommand.result in capsys.readouterr().out) is should_display


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


def test_pathflow_reports_an_invalid_operation_from_parser(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    stub_parser(monkeypatch, parser_result("unexpected"))

    cli.pathflow([])

    assert "Invalid Operator" in capsys.readouterr().out


def test_pathflow_accepts_no_explicit_argument_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received_args = stub_parser(monkeypatch, parser_result("unexpected"))

    cli.pathflow()

    assert received_args == [None]
