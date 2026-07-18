
import argparse
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.prompt import Prompt

from workflow.cli import workflow
from workflow.exceptions import ForceStop, WorkFlowInvalidOperation


class ExecuteWorkflow:
    def __init__(self, workflow_data : dict[Any, Any], args : argparse.Namespace) -> None:
        self.workflow_data = workflow_data
        self.args = args

        self.workspace_path = Path(self.workflow_data["meta-data"]["workspace"]).resolve()
        self.allow = True
        self.force = self.workflow_data["meta-data"]["force"]
        self.dry_run = self.workflow_data["meta-data"]["dry_run"]
        self.show_status = self.workflow_data["meta-data"].get("show_status", False)

        self.sequence_execution_commands : list[list[str]] = list()

    def construct_command(self) -> None:
        self.sequence_execution_commands.clear()

        initial_command : list[str] = ["-ws", str(self.workspace_path), "-a"]
        if self.force:
            initial_command.append("-f")
        if self.show_status:
            initial_command.append("-s")
        if self.dry_run:
            initial_command.append("-d")
        
        for action_data in self.workflow_data["actions"]:
            match action_data["operation"]:
                case "create":
                    create_command = ["create"]
                    if action_data["recursive"]:
                        create_command.append("-r")
                    create_command.append(action_data["type"])
                    create_command.append(self._path_argument(action_data["path"]))
                    self.sequence_execution_commands.append(initial_command + create_command)
                case "copy":
                    copy_command = [
                        "copy",
                        self._path_argument(action_data["source_path"]),
                        self._path_argument(action_data["destination_path"]),
                    ]
                    self.sequence_execution_commands.append(initial_command + copy_command)
                case "move":
                    move_command = [
                        "move",
                        self._path_argument(action_data["source_path"]),
                        self._path_argument(action_data["destination_path"]),
                    ]
                    self.sequence_execution_commands.append(initial_command + move_command)
                case "rename":
                    rename_command = [
                        "rename",
                        self._path_argument(action_data["path"]),
                        str(action_data["new_name"]),
                    ]
                    self.sequence_execution_commands.append(initial_command + rename_command)
                case "delete":
                    delete_command = [
                        "delete",
                        self._path_argument(action_data["path"]),
                    ]
                    self.sequence_execution_commands.append(initial_command + delete_command)
                case _:
                    raise WorkFlowInvalidOperation(
                        f"Cannot construct action {action_data.get('id')}: "
                        f"operation {action_data.get('operation')!r} is unsupported."
                    )

    def _path_argument(self, path_value: Any) -> str:
        path = Path(path_value)
        if not path.is_absolute():
            path = self.workspace_path / path
        return str(path)

    def execute_commands(self) -> None:
        self.construct_command()
        for id, command in enumerate(self.sequence_execution_commands, start=1):
            response = workflow(command)
            if response == 1:
                Console().print(f"A Unexpected Error Occurred when executing action {id}") # again why would this trigger. unless world is against you or your computer betrayed you (remember i have this project under MIT. so don't blame me)
                if self.permission_func("I recommend you pause the execution"):
                    raise ForceStop("Halting workflow due to unexpected error")

    def permission_func(self,prompt : str) -> bool:
        response = Prompt.ask(prompt=prompt, choices=["yes", "no"], case_sensitive=False, default="no")
        if response == "yes":
            return True
        else:
            return False    
