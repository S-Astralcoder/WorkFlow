import pytest

from pathflow.command_line import CommandLine


@pytest.fixture
def command_line() -> CommandLine:
    return CommandLine()


@pytest.mark.parametrize(
    ("args", "expected_error"),
    [
        ([], "the following arguments are required: operation"),
        (["unknown"], "invalid choice: 'unknown'"),
        (["create"], "the following arguments are required: TYPE, PATH"),
        (["create", "file"], "the following arguments are required: PATH"),
        (["copy", "source"], "the following arguments are required: destination_path"),
        (["move", "source"], "the following arguments are required: destination_path"),
        (["rename", "path"], "the following arguments are required: new_name"),
        (["delete"], "the following arguments are required: path"),
    ],
)
def test_missing_or_unknown_arguments_exit_with_usage_error(
    command_line: CommandLine,
    capsys: pytest.CaptureFixture[str],
    args: list[str],
    expected_error: str,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        command_line.get_parser(args)

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "usage:" in captured.err
    assert expected_error in captured.err
    assert captured.out == ""


@pytest.mark.parametrize("invalid_type", ["directory", "FILE", "", "file.txt"])
def test_create_rejects_invalid_item_type(
    command_line: CommandLine,
    capsys: pytest.CaptureFixture[str],
    invalid_type: str,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        command_line.get_parser(["create", invalid_type, "target"])

    assert exc_info.value.code == 2
    assert f"invalid choice: '{invalid_type}'" in capsys.readouterr().err


@pytest.mark.parametrize(
    "args",
    [
        ["delete", "target", "unexpected"],
        ["copy", "source", "destination", "unexpected"],
        ["rename", "target", "new-name", "unexpected"],
    ],
)
def test_rejects_extra_positional_arguments(
    command_line: CommandLine,
    capsys: pytest.CaptureFixture[str],
    args: list[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        command_line.get_parser(args)

    assert exc_info.value.code == 2
    assert "unrecognized arguments: unexpected" in capsys.readouterr().err


def test_workspace_option_requires_a_value(
    command_line: CommandLine,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        command_line.get_parser(["--workspace"])

    assert exc_info.value.code == 2
    assert "argument -ws/--workspace: expected one argument" in capsys.readouterr().err


@pytest.mark.parametrize("option", ["--allow", "--force", "--dry-run", "--show-status"])
def test_global_flags_after_operation_are_rejected(
    command_line: CommandLine,
    capsys: pytest.CaptureFixture[str],
    option: str,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        command_line.get_parser(["delete", "target", option])

    assert exc_info.value.code == 2
    assert f"unrecognized arguments: {option}" in capsys.readouterr().err


def test_option_like_path_is_rejected_without_end_of_options_marker(
    command_line: CommandLine,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        command_line.get_parser(["delete", "--looks-like-an-option"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "the following arguments are required: path" in captured.err


def test_end_of_options_marker_allows_option_like_path(command_line: CommandLine) -> None:
    parsed = command_line.get_parser(["delete", "--", "--looks-like-an-option"])

    assert parsed.operation == "delete"
    assert parsed.path == "--looks-like-an-option"
