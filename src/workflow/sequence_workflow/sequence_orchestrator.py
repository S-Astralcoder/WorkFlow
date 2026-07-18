from pathlib import Path
from typing import Any

from rich.console import Console

from workflow.exceptions import VirtualAlreadyExists, VirtualInvalidItemType, VirtualNameInvalid, VirtualParentAbsent, VirtualTypeCollision, WorkFlowError, WorkFlowInvalidOperation, WorkFlowPathOutOfScope
from workflow.safety import FileSafety
from workflow.sequence_workflow.virtual_tree import VirtualTree, to_rich_tree


class SequenceOperations:
    def __init__(self, workflow_data: dict[Any, Any]) -> None:
        self.error_cache : dict[Any, Any] = dict()
        
        
        self.workflow_data = workflow_data
        
        self.root_path : Path = Path(self.workflow_data["meta-data"].get("workspace"))
        self.force = self.workflow_data["meta-data"].get("force")
        self.dry_run = self.workflow_data["meta-data"].get("dry_run")
        self.allow = self.workflow_data["meta-data"].get("allow")
        self.show_status = self.workflow_data["meta-data"].get("show_status")

        self.virtual_tree = VirtualTree(root_name=self.root_path.name)

    def load_workspace_virtual_tree(self) -> None: # Not optimized for large workspace
        for child in self.root_path.rglob("*"):
            relative_path = child.relative_to(self.root_path)
            end_type = "folder"
            if FileSafety.check_if_file(path=child):
                end_type = "file"
            self.virtual_tree.add_path(relative_path=relative_path.parts, end_type=end_type, recursive=True, force=True)
        
        Console().print(to_rich_tree(self.virtual_tree.root_node))

    def validate_create_and_update_state(self, action_data: dict[Any, Any]) -> None:
        path = Path(action_data["path"])
        if not self.within_workspace_scope(workspace=self.root_path, path=path):
            self.error_cache.setdefault(action_data["id"], WorkFlowPathOutOfScope("The given path is out of workspace scope"))
            return
        try:
            relative_path = path.relative_to(self.root_path)
            self.virtual_tree.add_path(relative_path=relative_path.parts, end_type=action_data["type"], recursive=action_data["recursive"], force=self.force)
        except (VirtualNameInvalid, VirtualAlreadyExists, VirtualInvalidItemType, VirtualParentAbsent, VirtualTypeCollision) as e:
            self.error_cache.setdefault(action_data["id"], WorkFlowError(e))



    def validate_copy_and_update_state(self, action_data: dict[Any, Any]) -> None:
        pass

    def validate_move_and_update_state(self, action_data: dict[Any, Any]) -> None:
        pass

    def _validate_name(self, new_name: str, path: Path) -> Path:
        raise NotImplementedError

    def validate_rename_and_update_state(self, action_data: dict[Any, Any]) -> None:
        pass

    def validate_delete_and_update_state(self, action_data: dict[Any, Any]) -> None:
        pass

    def validate_sequence_operation(self) -> None:
        for action_data in self.workflow_data["actions"]:
            match action_data["operation"]:
                case "create":
                    self.validate_create_and_update_state(action_data=action_data)
                case _:
                    self.error_cache.setdefault(action_data["id"], WorkFlowInvalidOperation("The Given operation is invalid"))

    
    def within_workspace_scope(self, workspace : Path, path : Path):
        if FileSafety.is_relative_to(path1=workspace, path2=path):
            return True
        return False