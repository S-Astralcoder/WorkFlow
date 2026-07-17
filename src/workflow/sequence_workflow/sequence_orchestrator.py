from pathlib import Path
from typing import Any


class SequenceOperations:
    def __init__(self, workflow_data: dict[Any, Any]) -> None:
        self.workflow_data = workflow_data

    def initial_setup(self) -> None:
        pass

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
