# External 
import argparse
from pathlib import Path
import tomllib
from typing import Any
import os

# Internal
from workflow.exceptions import InvalidFilePath, InvalidFileType, InvalidWorkFlowScript, WorkflowPathInvalid
from workflow.safety import FileSafety

class WorkFlowConstructor:
    def __init__(self, args : argparse.Namespace) -> None:
        self.args = args
        self.workflow_path = self._validate_workflow(path=args.workflow_path)

        self.raw_workflow_data = self._fetch_workflow_data()

        self.workflow_data = dict[str, Any]()  

        self._format_raw_data()

    def _validate_workflow(self, path : str) -> Path:
        if not FileSafety.valid_path_string(path=path):
            raise InvalidFilePath(f"Invalid workflow path '{path}': the value is not a valid filesystem path.")
        workflow_path = Path(path)
        if not FileSafety.does_exists(path=workflow_path):
            raise WorkflowPathInvalid(f"Workflow script '{workflow_path.resolve()}' does not exist.")
        if not (FileSafety.check_if_file(path=workflow_path) and FileSafety.check_if_toml_file(path=workflow_path)):
            raise InvalidFileType(f"Workflow script '{workflow_path.resolve()}' must be an existing .toml file.")
        return workflow_path

    def _validate_path(self, path : str) -> str:
        if not FileSafety.valid_path_string(path=path):
            raise InvalidFilePath(f"Invalid workspace path '{path}': the value is not a valid filesystem path.")
        workflow_path = Path(path)
        if not FileSafety.does_exists(path=workflow_path):
            raise WorkflowPathInvalid(f"Workflow workspace '{workflow_path.resolve()}' does not exist.")
        return str(workflow_path.resolve())

    def _fetch_workflow_data(self) -> dict[Any, Any]:
        with open(self.workflow_path, "rb") as file:
            workflow_data = tomllib.load(file)
        return workflow_data


    def construct_workflow_head(self) -> None:
        workflow = self.raw_workflow_data["workflow"]
        name = workflow.get("name")
        workspace = getattr(self.args, "workspace", ".")
        if workspace != "*":
            if workspace == ".":
                workspace = workflow.get("workspace")
        else:
            workspace = "."
        force = getattr(self.args, "force", False) or workflow.get("force", False)
        dry_run = getattr(self.args, "dry_run", False) or workflow.get("dry_run", False)
        allow = getattr(self.args, "allow", False) or workflow.get("allow", False)
        show_status = getattr(self.args, "show_status", False) or workflow.get("show", False)
        self.workflow_data["meta-data"] = {"name" : name, "workspace" : self._validate_path(workspace), "force" : force, "dry_run" : dry_run, "allow" : allow, "show_status" : show_status} 


    def construct_create(self, create_action : dict[Any, Any], action_id : int) -> None:
        type = create_action.get("type")
        path = create_action.get("path")
        if None in (type, path):
            raise InvalidWorkFlowScript(f"Action {action_id} ('create') is invalid: required fields are 'type' and 'path'; received type={type!r}, path={path!r}.")
        
        self.workflow_data["actions"].append({"id" : action_id ,"operation" : "create", "type" : type, "path" : Path(path).resolve(), "recursive" : create_action.get("recursive", False)})  # pyright: ignore[reportArgumentType]

    def construct_copy(self, copy_action : dict[Any, Any], action_id : int) -> None:
        source_path = copy_action.get("source_path")
        destination_path = copy_action.get("destination_path")
        if None in (source_path, destination_path):
            raise InvalidWorkFlowScript(f"Action {action_id} ('copy') is invalid: required fields are 'source_path' and 'destination_path'; received source_path={source_path!r}, destination_path={destination_path!r}.")
        self.workflow_data["actions"].append({"id" : action_id, "operation" : "copy", "source_path" : Path(source_path).resolve(), "destination_path" : Path(destination_path).resolve()})  # pyright: ignore[reportArgumentType]

    def construct_move(self, move_action : dict[Any, Any], action_id : int) -> None:
        source_path = move_action.get("source_path")
        destination_path = move_action.get("destination_path")
        if None in (source_path, destination_path):
            raise InvalidWorkFlowScript(f"Action {action_id} ('move') is invalid: required fields are 'source_path' and 'destination_path'; received source_path={source_path!r}, destination_path={destination_path!r}.")
        self.workflow_data["actions"].append({"id" : action_id, "operation" : "move", "source_path" : Path(source_path).resolve(), "destination_path" : Path(destination_path).resolve()})  # pyright: ignore[reportArgumentType]

    def construct_rename(self, rename_action : dict[Any, Any], action_id : int) -> None:
        path = rename_action.get("path")
        new_name = rename_action.get("new_name")
        if None in (path, new_name):
            raise InvalidWorkFlowScript(f"Action {action_id} ('rename') is invalid: required fields are 'path' and 'new_name'; received path={path!r}, new_name={new_name!r}.")
        self.workflow_data["actions"].append({"id" : action_id, "operation" : "rename", "path" : Path(path).resolve(), "new_name" : new_name})  # pyright: ignore[reportArgumentType]

    def construct_delete(self, delete_action : dict[Any, Any], action_id : int) -> None:
        path = delete_action.get("path")
        if path is None:
            raise InvalidWorkFlowScript(f"Action {action_id} ('delete') is invalid: required field 'path' is missing.")
        self.workflow_data["actions"].append({"id" : action_id, "operation" : "delete", "path" : Path(path).resolve()})

    def _format_raw_data(self) -> None:
        self.construct_workflow_head()

        working_dir = Path(self.workflow_data["meta-data"].get("workspace")).resolve()
        os.chdir(working_dir)

        self.workflow_data["actions"] = []

        for id, action_data in enumerate(self.raw_workflow_data["actions"], start=1):

            operation = action_data.get("operation")
            match operation:
                case "create":
                    self.construct_create(create_action=action_data, action_id=id)
                case "copy":
                    self.construct_copy(copy_action=action_data, action_id=id)
                case "move":
                    self.construct_move(move_action=action_data, action_id=id)
                case "rename":
                    self.construct_rename(rename_action=action_data, action_id=id)
                case "delete":
                    self.construct_delete(delete_action=action_data, action_id=id)
                case _:
                    raise InvalidWorkFlowScript(f"Action {id} has unsupported operation {operation!r}. Supported operations: create, copy, move, rename, delete.")
                
    def get_workspace_sequence_data(self):
        return self.workflow_data
