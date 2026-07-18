from pathlib import Path
from typing import Any

from workflow.exceptions import (
    VirtualAlreadyExists,
    VirtualCollisionError,
    VirtualDestinationNotExists,
    VirtualInvalidItemType,
    VirtualNameInvalid,
    VirtualOperationOnSelf,
    VirtualParentAbsent,
    VirtualPathNotExists,
    VirtualRenameAlreadyExists,
    VirtualRootProtection,
    VirtualSourceNotExists,
    VirtualSuffixMissMatch,
    VirtualTypeCollision,
    WorkFlowError,
    WorkFlowInvalidOperation,
    WorkFlowPathOutOfScope,
)
from workflow.safety import FileSafety
from workflow.sequence_workflow.virtual_tree import VirtualTree


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

    def validate_create_and_update_state(self, action_data: dict[Any, Any]) -> None:
        path = Path(action_data["path"])
        relative_path = self._relative_path_parts(
            action_id=action_data["id"],
            operation="create",
            path=path,
            path_label="target path",
        )
        if relative_path is None:
            return
        try:
            self.virtual_tree.add_path(relative_path=relative_path, end_type=action_data["type"], recursive=action_data["recursive"], force=self.force)
        except (VirtualNameInvalid, VirtualAlreadyExists, VirtualInvalidItemType, VirtualParentAbsent, VirtualTypeCollision, VirtualRootProtection) as e:
            self._cache_virtual_error(action_id=action_data["id"], operation="create", error=e)



    def validate_copy_and_update_state(self, action_data: dict[Any, Any]) -> None:
        source_path = Path(action_data["source_path"])
        destination_path = Path(action_data["destination_path"])

        relative_source_path = self._relative_path_parts(
            action_id=action_data["id"],
            operation="copy",
            path=source_path,
            path_label="source path",
        )
        if relative_source_path is None:
            return
        relative_destination_path = self._relative_path_parts(
            action_id=action_data["id"],
            operation="copy",
            path=destination_path,
            path_label="destination path",
        )
        if relative_destination_path is None:
            return

        try:
            self.virtual_tree.copy_path(
                relative_source_path=relative_source_path,
                relative_destination_path=relative_destination_path,
            )
        except (VirtualSourceNotExists, VirtualDestinationNotExists, VirtualCollisionError, VirtualInvalidItemType, VirtualOperationOnSelf, VirtualRootProtection) as e:
            self._cache_virtual_error(action_id=action_data["id"], operation="copy", error=e)

    def validate_move_and_update_state(self, action_data: dict[Any, Any]) -> None:
        source_path = Path(action_data["source_path"])
        destination_path = Path(action_data["destination_path"])

        relative_source_path = self._relative_path_parts(
            action_id=action_data["id"],
            operation="move",
            path=source_path,
            path_label="source path",
        )
        if relative_source_path is None:
            return
        relative_destination_path = self._relative_path_parts(
            action_id=action_data["id"],
            operation="move",
            path=destination_path,
            path_label="destination path",
        )
        if relative_destination_path is None:
            return

        try:
            self.virtual_tree.move_path(
                relative_source_path=relative_source_path,
                relative_destination_path=relative_destination_path,
            )
        except (VirtualSourceNotExists, VirtualDestinationNotExists, VirtualCollisionError, VirtualInvalidItemType, VirtualOperationOnSelf, VirtualRootProtection) as e:
            self._cache_virtual_error(action_id=action_data["id"], operation="move", error=e)

    def validate_rename_and_update_state(self, action_data: dict[Any, Any]) -> None:
        path = Path(action_data["path"])
        relative_path = self._relative_path_parts(
            action_id=action_data["id"],
            operation="rename",
            path=path,
            path_label="source path",
        )
        if relative_path is None:
            return

        try:
            self.virtual_tree.rename_path_node(
                relative_path=relative_path,
                new_name=action_data["new_name"],
                force=self.force,
            )
        except (VirtualPathNotExists, VirtualNameInvalid, VirtualOperationOnSelf, VirtualSuffixMissMatch, VirtualRenameAlreadyExists, VirtualRootProtection) as e:
            self._cache_virtual_error(action_id=action_data["id"], operation="rename", error=e)

    def validate_delete_and_update_state(self, action_data: dict[Any, Any]) -> None:
        path = Path(action_data["path"])
        relative_path = self._relative_path_parts(
            action_id=action_data["id"],
            operation="delete",
            path=path,
            path_label="target path",
        )
        if relative_path is None:
            return

        try:
            self.virtual_tree.remove_path(relative_path=relative_path)
        except (VirtualPathNotExists, VirtualRootProtection) as e:
            self._cache_virtual_error(action_id=action_data["id"], operation="delete", error=e)

    def validate_sequence_operation(self) -> None:
        for action_data in self.workflow_data["actions"]:
            match action_data["operation"]:
                case "create":
                    self.validate_create_and_update_state(action_data=action_data)
                case "copy":
                    self.validate_copy_and_update_state(action_data=action_data)
                case "move":
                    self.validate_move_and_update_state(action_data=action_data)
                case "rename":
                    self.validate_rename_and_update_state(action_data=action_data)
                case "delete":
                    self.validate_delete_and_update_state(action_data=action_data)
                case _:
                    operation = action_data.get("operation")
                    self.error_cache.setdefault(
                        action_data["id"],
                        WorkFlowInvalidOperation(
                            f"Action {action_data['id']} has unsupported operation {operation!r}. "
                            "Supported operations are: create, copy, move, rename, and delete."
                        ),
                    )

    def _relative_path_parts(self, action_id: Any, operation: str, path: Path, path_label: str) -> tuple[str, ...] | None:
        if not self.within_workspace_scope(workspace=self.root_path, path=path):
            self.error_cache.setdefault(
                action_id,
                WorkFlowPathOutOfScope(
                    f"Action {action_id} ('{operation}') would fail: {path_label} '{path}' "
                    f"is outside workspace '{self.root_path}'."
                ),
            )
            return None
        return path.relative_to(self.root_path).parts

    def _cache_virtual_error(self, action_id: Any, operation: str, error: Exception) -> None:
        self.error_cache.setdefault(
            action_id,
            WorkFlowError(f"Action {action_id} ('{operation}') would fail: {error}"),
        )

    def within_workspace_scope(self, workspace : Path, path : Path):
        if FileSafety.is_relative_to(path1=workspace, path2=path):
            return True
        return False
