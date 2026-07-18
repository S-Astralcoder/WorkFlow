import argparse
from pathlib import Path
import tomllib
from typing import Any, cast

from workflow.exceptions import (
    InvalidFilePath,
    InvalidFileType,
    InvalidWorkFlowScript,
    WorkflowPathInvalid,
)
from workflow.safety import FileSafety


class WorkFlowConstructor:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.workflow_path = self._validate_workflow(path=args.workflow_path)
        self.raw_workflow_data = self._fetch_workflow_data()
        self.workflow_data: dict[str, Any] = {}
        self.workspace_path: Path
        self._format_raw_data()

    def _validate_workflow(self, path: str) -> Path:
        if not FileSafety.valid_path_string(path=path):
            raise InvalidFilePath(
                f"Invalid workflow path '{path}': provide a valid path to a TOML file."
            )
        workflow_path = Path(path)
        if not FileSafety.does_exists(path=workflow_path):
            raise WorkflowPathInvalid(
                f"Workflow script '{workflow_path.resolve()}' does not exist."
            )
        if not (
            FileSafety.check_if_file(path=workflow_path)
            and FileSafety.check_if_toml_file(path=workflow_path)
        ):
            raise InvalidFileType(
                f"Workflow script '{workflow_path.resolve()}' must be an existing .toml file."
            )
        return workflow_path

    def _validate_workspace(self, path: str) -> Path:
        if not FileSafety.valid_path_string(path=path):
            raise InvalidFilePath(
                f"Invalid workflow workspace '{path}': provide a valid folder path."
            )
        workspace_path = Path(path).resolve()
        if not FileSafety.does_exists(path=workspace_path):
            raise WorkflowPathInvalid(
                f"Workflow workspace '{workspace_path}' does not exist. Create it first or choose another folder."
            )
        if FileSafety.check_if_file(path=workspace_path):
            raise WorkflowPathInvalid(
                f"Workflow workspace '{workspace_path}' is a file. Choose a folder instead."
            )
        return workspace_path

    def _fetch_workflow_data(self) -> dict[str, Any]:
        try:
            with open(self.workflow_path, "rb") as file:
                return tomllib.load(file)
        except tomllib.TOMLDecodeError as error:
            raise InvalidWorkFlowScript(
                f"Workflow script '{self.workflow_path}' contains invalid TOML: {error}"
            ) from None

    @staticmethod
    def _required_string(value: object, field: str, context: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise InvalidWorkFlowScript(
                f"{context} requires non-empty string field '{field}'; received {value!r}."
            )
        return value

    @staticmethod
    def _optional_bool(
        data: dict[str, Any], field: str, context: str, default: bool = False
    ) -> bool:
        value = data.get(field, default)
        if not isinstance(value, bool):
            raise InvalidWorkFlowScript(
                f"{context} field '{field}' must be true or false; received {value!r}."
            )
        return value

    def _action_path(self, value: object, field: str, action_id: int) -> Path:
        raw_path = self._required_string(value, field, f"Action {action_id}")
        path = Path(raw_path)
        if not path.is_absolute():
            path = self.workspace_path / path
        return path.resolve()

    def construct_workflow_head(self) -> None:
        workflow_value = self.raw_workflow_data.get("workflow")
        if not isinstance(workflow_value, dict):
            raise InvalidWorkFlowScript(
                "Workflow script requires a [workflow] table."
            )
        workflow = cast(dict[str, Any], workflow_value)

        name = workflow.get("name")
        if name is not None and not isinstance(name, str):
            raise InvalidWorkFlowScript(
                f"Workflow field 'name' must be a string; received {name!r}."
            )

        configured_workspace = getattr(self.args, "workspace", ".")
        if configured_workspace == "*":
            workspace = "."
        elif configured_workspace == ".":
            workspace = workflow.get("workspace")
        else:
            workspace = configured_workspace
        workspace = self._required_string(
            workspace, "workspace", "Workflow configuration"
        )
        self.workspace_path = self._validate_workspace(workspace)

        force = getattr(self.args, "force", False) or self._optional_bool(
            workflow, "force", "Workflow configuration"
        )
        dry_run = getattr(self.args, "dry_run", False) or self._optional_bool(
            workflow, "dry_run", "Workflow configuration"
        )
        allow = getattr(self.args, "allow", False) or self._optional_bool(
            workflow, "allow", "Workflow configuration"
        )
        show_status = getattr(
            self.args, "show_status", False
        ) or self._optional_bool(workflow, "show", "Workflow configuration")

        self.workflow_data["meta-data"] = {
            "name": name,
            "workspace": str(self.workspace_path),
            "force": force,
            "dry_run": dry_run,
            "allow": allow,
            "show_status": show_status,
        }

    def construct_create(
        self, create_action: dict[str, Any], action_id: int
    ) -> None:
        item_type = create_action.get("type")
        if item_type not in {"file", "folder"}:
            raise InvalidWorkFlowScript(
                f"Action {action_id} ('create') field 'type' must be 'file' or 'folder'; "
                f"received {item_type!r}."
            )
        path = self._action_path(create_action.get("path"), "path", action_id)
        recursive = self._optional_bool(
            create_action, "recursive", f"Action {action_id} ('create')"
        )
        self.workflow_data["actions"].append(
            {
                "id": action_id,
                "operation": "create",
                "type": item_type,
                "path": path,
                "recursive": recursive,
            }
        )

    def construct_copy(self, copy_action: dict[str, Any], action_id: int) -> None:
        source_path = self._action_path(
            copy_action.get("source_path"), "source_path", action_id
        )
        destination_path = self._action_path(
            copy_action.get("destination_path"), "destination_path", action_id
        )
        self.workflow_data["actions"].append(
            {
                "id": action_id,
                "operation": "copy",
                "source_path": source_path,
                "destination_path": destination_path,
            }
        )

    def construct_move(self, move_action: dict[str, Any], action_id: int) -> None:
        source_path = self._action_path(
            move_action.get("source_path"), "source_path", action_id
        )
        destination_path = self._action_path(
            move_action.get("destination_path"), "destination_path", action_id
        )
        self.workflow_data["actions"].append(
            {
                "id": action_id,
                "operation": "move",
                "source_path": source_path,
                "destination_path": destination_path,
            }
        )

    def construct_rename(
        self, rename_action: dict[str, Any], action_id: int
    ) -> None:
        path = self._action_path(rename_action.get("path"), "path", action_id)
        new_name = self._required_string(
            rename_action.get("new_name"), "new_name", f"Action {action_id} ('rename')"
        )
        self.workflow_data["actions"].append(
            {
                "id": action_id,
                "operation": "rename",
                "path": path,
                "new_name": new_name,
            }
        )

    def construct_delete(
        self, delete_action: dict[str, Any], action_id: int
    ) -> None:
        path = self._action_path(delete_action.get("path"), "path", action_id)
        self.workflow_data["actions"].append(
            {"id": action_id, "operation": "delete", "path": path}
        )

    def _format_raw_data(self) -> None:
        self.construct_workflow_head()
        actions_value = self.raw_workflow_data.get("actions")
        if not isinstance(actions_value, list) or not actions_value:
            raise InvalidWorkFlowScript(
                "Workflow script requires one or more [[actions]] tables."
            )
        actions = cast(list[Any], actions_value)

        self.workflow_data["actions"] = []
        for action_id, action_value in enumerate(actions, start=1):
            if not isinstance(action_value, dict):
                raise InvalidWorkFlowScript(
                    f"Action {action_id} must be a TOML table."
                )
            action_data = cast(dict[str, Any], action_value)

            operation = action_data.get("operation")
            match operation:
                case "create":
                    self.construct_create(
                        create_action=action_data, action_id=action_id
                    )
                case "copy":
                    self.construct_copy(copy_action=action_data, action_id=action_id)
                case "move":
                    self.construct_move(move_action=action_data, action_id=action_id)
                case "rename":
                    self.construct_rename(
                        rename_action=action_data, action_id=action_id
                    )
                case "delete":
                    self.construct_delete(
                        delete_action=action_data, action_id=action_id
                    )
                case _:
                    raise InvalidWorkFlowScript(
                        f"Action {action_id} has unsupported operation {operation!r}. "
                        "Supported operations are: create, copy, move, rename, and delete."
                    )

    def get_workspace_sequence_data(self) -> dict[str, Any]:
        return self.workflow_data
