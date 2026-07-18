from pathlib import Path
from typing import Any

from rich.console import Console

from workflow.safety import FileSafety
from workflow.sequence_workflow.virtual_tree import VirtualTree, to_rich_tree


class SequenceOperations:
    def __init__(self, workflow_data: dict[Any, Any]) -> None:
        self.workflow_data = workflow_data
        
        self.root_path : Path = Path(self.workflow_data["meta-data"].get("workspace"))
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
        pass

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
        pass

    def validate_workspace_scope(
        self,
        workspace: Path,
        path: Path,
        inside: bool = True,
    ) -> None:
        pass
