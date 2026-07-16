# External 
from pathlib import Path
import tomllib
from typing import Any

from workflow.exceptions import InvalidFilePath, InvalidFileType, WorkflowPathInvalid
from workflow.safety import FileSafety



class WorkFlowConstructor:
    def __init__(self, workflow_path : str) -> None:
        self.workflow_path = self._validate_workflow(path=workflow_path)

        self.raw_workflow_data = self._fetch_workflow_data()

    def _validate_workflow(self, path : str) -> Path:
        if not FileSafety.valid_path_string(path=path):
            raise InvalidFilePath("The Given path is invalid; enter a valid workflow path")
        workflow_path = Path(path)
        if not FileSafety.does_exists(path=workflow_path):
            raise WorkflowPathInvalid("The Given workflow path doesn't exists")
        if not (FileSafety.check_if_file(path=workflow_path) and FileSafety.check_if_toml_file(path=workflow_path)):
            raise InvalidFileType("The workflow path should be .toml file") 
        return workflow_path

    def _fetch_workflow_data(self) -> dict[Any, Any]:
        with open(self.workflow_path, "rb") as file:
            workflow_data = tomllib.load(file)
        return workflow_data


    def construct_workflow_head(self):
        pass


    def _format_raw_data(self):
        pass
