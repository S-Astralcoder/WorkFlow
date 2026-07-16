
import pathlib
from typing import Any

from workflow.exceptions import InvalidWorkFlowScript


class SequenceOperations:
    def __init__(self, workflow_data : dict[Any, Any]) -> None:
        self.workflow_data = workflow_data

        self.workspace = pathlib.Path(self.workflow_data["meta-data"].get("workspace")).resolve()

        # internal space
        self.would_exits : set[pathlib.Path] = set()
        self.would_removed : set[pathlib.Path] = set()


    def initial_setup(self):
        self.would_exits.add(self.workspace)

    def validate_create_and_update_state(self, action_data : dict[Any, Any]):
        pass


    def validate_sequence_operation(self):
        for action_data in self.workflow_data["actions"]:
            match action_data.get("operation"):
                case "create":
                    pass
                case _:
                    raise InvalidWorkFlowScript(f"Invalid operation for action {action_data.get("id")}")

