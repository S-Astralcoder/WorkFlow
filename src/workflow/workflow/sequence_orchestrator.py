
from pathlib import Path
from typing import Any

from workflow.exceptions import InvalidFileName, InvalidWorkFlowScript, OutOfScope, WorkspaceProtection
from workflow.safety import FileSafety


class SequenceOperations:
    def __init__(self, workflow_data : dict[Any, Any]) -> None:
        self.workflow_data = workflow_data

        self.force = self.workflow_data["meta-data"].get("force")

        self.workspace = Path(self.workflow_data["meta-data"].get("workspace")).resolve()

        # internal space
        self.would_exits : set[Path] = set() # Update to tree structure in next version. when implementing full scale dynamic execution
        self.would_removed : set[Path] = set()

        self.exists_file : set[Path] = set()
        self.removed_file : set[Path] = set()

        # don't ask why i didn't use tree here. i just wanted to test stuff 

        self.initial_setup()
        self.validate_sequence_operation()

        # No i was crazy


    def initial_setup(self):
        self.would_exits.add(self.workspace.resolve())

    def validate_create_and_update_state(self, action_data : dict[Any, Any]):
        path = Path(action_data.get("path")).resolve()  # pyright: ignore[reportArgumentType]
        recursive = action_data.get("recursive")
        try:
            self.validate_workspace_scope(self.workspace, path)  
        except SystemExit as e:
            raise InvalidWorkFlowScript(e) # unnecessary double raise but nah lets to it for consistency
        if not recursive:
            if not FileSafety.does_exists(path.parent) or path.parent.resolve() in self.would_removed:
                if path.parent.resolve() not in self.would_exits:
                    raise InvalidWorkFlowScript(f"The parent for the operation create in action {action_data.get("id")} doesn't exist, use --recursive")
            self.would_exits.add(path.resolve())
            self.would_removed.discard(path.resolve())
        else:
            recursive_path = path
            while recursive_path.resolve() not in self.would_exits:
                self.would_exits.add(recursive_path.resolve())
                self.would_removed.discard(recursive_path.resolve())
                recursive_path = recursive_path.parent

    def validate_copy_and_update_state(self, action_data : dict[Any, Any]):
        source_path = Path(action_data.get("source_path")).resolve()  # pyright: ignore[reportArgumentType]
        destination_path = Path(action_data.get("destination_path")).resolve()  # pyright: ignore[reportArgumentType]
        try:
            self.validate_workspace_scope(self.workspace, source_path)  
            self.validate_workspace_scope(self.workspace, destination_path, inside=False)  
        except SystemExit as e:
            raise InvalidWorkFlowScript(e) 

        from_state_space : bool = False

        # source validation
        if not FileSafety.does_exists(path=source_path):
            if source_path.resolve() not in self.would_exits or source_path.resolve() in self.would_removed:
                raise InvalidWorkFlowScript(f"The given source path to be copied doesn't exist in action {action_data.get("id")}")
            from_state_space = True
        if not self.force:
            target_des = destination_path / source_path.name
            if FileSafety.does_exists(path=target_des):
                if target_des.resolve() not in self.would_removed:
                    raise InvalidWorkFlowScript(f"The given source already exists in destination in action {action_data.get("id")}")

        if not FileSafety.does_exists(path=destination_path) or destination_path.resolve() in self.would_removed:
            if destination_path.resolve() not in self.would_exits:
                raise InvalidWorkFlowScript(f"The given destination doesn't exist in action {action_data.get("id")}")

        if FileSafety.check_if_file(path=destination_path):
            raise InvalidWorkFlowScript(f"The given destination should be a folder in action {action_data.get("id")}")

        if FileSafety.is_relative_to(path1=source_path, path2=destination_path):
            raise InvalidWorkFlowScript(f"Coping itself to it's own child is not allowed in action {action_data.get("id")}")
        
        if not FileSafety.check_if_file(path=source_path):
            if from_state_space:
                new_virtual_paths : list[Path] = []
                for virtual_path in self.would_exits:
                    if FileSafety.is_relative_to(path1=source_path, path2=virtual_path):
                        relative_path = virtual_path.relative_to(source_path)
                        new_virtual_path = destination_path / source_path.name / relative_path
                        new_virtual_paths.append(new_virtual_path.resolve())
                self.would_exits.update(new_virtual_paths)
                self.would_removed.difference_update(new_virtual_paths)
            else:
                new_virtual_path = destination_path / source_path.name
                self.would_exits.add(new_virtual_path.resolve())
                self.would_removed.discard(new_virtual_path.resolve())
                for child in source_path.rglob("*"):
                    relative_path = child.relative_to(source_path)
                    new_virtual_path = destination_path / source_path.name / relative_path
                    self.would_exits.add(new_virtual_path.resolve())
                    self.would_removed.discard(new_virtual_path.resolve())
        else:
            new_virtual_path = destination_path / source_path.name
            self.would_exits.add(new_virtual_path.resolve())
            self.would_removed.discard(new_virtual_path.resolve())

    def validate_move_and_update_state(self, action_data : dict[Any, Any]):
        source_path = Path(action_data.get("source_path")).resolve()  # pyright: ignore[reportArgumentType]
        destination_path = Path(action_data.get("destination_path")).resolve()  # pyright: ignore[reportArgumentType]
        try:
            self.validate_workspace_scope(self.workspace, source_path)  
            self.validate_workspace_scope(self.workspace, destination_path)  
        except SystemExit as e:
            raise InvalidWorkFlowScript(e) 

        from_state_space : bool = False

        # source validation
        if not FileSafety.does_exists(path=source_path):
            if source_path.resolve() not in self.would_exits or source_path.resolve() in self.would_removed:
                raise InvalidWorkFlowScript(f"The given source path to be copied doesn't exist in action {action_data.get("id")}")
            from_state_space = True
        if not self.force:
            target_des = destination_path / source_path.name
            if FileSafety.does_exists(path=target_des):
                if target_des.resolve() not in self.would_removed:
                    raise InvalidWorkFlowScript(f"The given source already exists in destination in action {action_data.get("id")}")

        if not FileSafety.does_exists(path=destination_path) or destination_path.resolve() in self.would_removed:
            if destination_path.resolve() not in self.would_exits:
                raise InvalidWorkFlowScript(f"The given destination doesn't exist in action {action_data.get("id")}")
        
        if FileSafety.check_if_file(path=destination_path):
            raise InvalidWorkFlowScript(f"The given destination should be a folder in action {action_data.get("id")}")

        if FileSafety.is_relative_to(path1=source_path, path2=destination_path):
            raise InvalidWorkFlowScript(f"Moving itself to it's own child is not allowed in action {action_data.get("id")}")
        
        if not FileSafety.check_if_file(path=source_path):
            if from_state_space:
                new_virtual_paths : list[Path] = []
                removed_virtual_paths : list[Path] = []
                for virtual_path in self.would_exits:
                    if FileSafety.is_relative_to(path1=source_path, path2=virtual_path):
                        relative_path = virtual_path.relative_to(source_path)
                        new_virtual_path = destination_path / source_path.name / relative_path
                        new_virtual_paths.append(new_virtual_path.resolve())
                        removed_virtual_paths.append(virtual_path.resolve())
                self.would_exits.update(new_virtual_paths)
                self.would_removed.update(removed_virtual_paths)
                self.would_removed.difference_update(new_virtual_paths)
                for paths in self.would_removed:
                    self.would_exits.discard(paths.resolve())
            else:
                self.would_removed.add(source_path.resolve())
                new_virtual_path = destination_path / source_path.name
                self.would_exits.add(new_virtual_path.resolve())
                self.would_removed.discard(new_virtual_path.resolve())
                for child in source_path.rglob("*"):
                    relative_path = child.relative_to(source_path)
                    new_virtual_path = destination_path / source_path.name / relative_path
                    self.would_exits.add(new_virtual_path.resolve())
                    self.would_removed.discard(new_virtual_path.resolve())
                    self.would_removed.add(child.resolve())
        else:
            new_virtual_path = destination_path / source_path.name
            self.would_exits.add(new_virtual_path.resolve())
            self.would_removed.add(source_path.resolve())
            self.would_exits.discard(source_path.resolve())
            self.would_removed.discard(new_virtual_path.resolve())


    def _validate_name(self, new_name : str, path : Path) -> Path:
        if not FileSafety.check_if_valid_name(name=new_name):
            raise InvalidFileName("Invalid new name: provide a valid file or folder name without a path.")
        return path.parent / Path(new_name).name

    def validate_rename_and_update_state(self, action_data : dict[Any, Any]):
        from_state_space = False
        path = Path(action_data.get("path")).resolve()  # pyright: ignore[reportArgumentType]
        try:
            self.validate_workspace_scope(self.workspace, path)
            new_name = self._validate_name(action_data.get("new_name"), path=path)    # pyright: ignore[reportArgumentType]
        except SystemExit as e:
            raise InvalidWorkFlowScript(e) 

        if not FileSafety.does_exists(path=path) or path.resolve() in self.would_removed:
            if path.resolve() not in self.would_exits:
                raise InvalidWorkFlowScript(f"The give source doesn't exist at action {action_data.get("id")}")
            from_state_space = True
        
            

        if not self.force:
            if FileSafety.check_if_file(path=path) and path.suffix != Path(new_name).suffix:
                raise InvalidWorkFlowScript("The new filename uses a different extension. Keep the original extension or use --force to allow the change.")

            if (FileSafety.does_exists(path=new_name) or new_name.resolve() in self.would_exits) and new_name.resolve() not in self.would_removed:
                raise InvalidWorkFlowScript("The new name already exist's")

        if from_state_space:
            changed_paths : list[Path] = []

            for virtual_paths in self.would_exits:
                if FileSafety.is_relative_to(path1=path.resolve(), path2=virtual_paths.resolve()):
                    changed_paths.append(virtual_paths.resolve())

            for change_path in changed_paths:
                self.would_removed.add(change_path.resolve())
                self.would_exits.discard(change_path.resolve())

                relative_path = change_path.relative_to(path)
                new_virtual_path = new_name / relative_path

                self.would_exits.add(new_virtual_path.resolve())
                self.would_removed.discard(new_virtual_path.resolve())
        else:
            head_virtual_path = new_name
            self.would_exits.add(head_virtual_path.resolve())
            self.would_removed.discard(head_virtual_path.resolve())

            for children in path.rglob("*"):
                relative_path = children.relative_to(path)
                virtual_paths = new_name / relative_path
                self.would_exits.add(virtual_paths.resolve())
                self.would_removed.discard(virtual_paths.resolve())

            



    
    def validate_delete_and_update_state(self, action_data : dict[Any, Any]):
        from_state_space = False

        path = Path(action_data.get("path")).resolve()  # pyright: ignore[reportArgumentType]
        try:
            self.validate_workspace_scope(self.workspace, path)
        except SystemExit as e:
            raise InvalidWorkFlowScript(e) 

        if not FileSafety.does_exists(path=path) or path.resolve() in self.would_removed:
            if path.resolve() not in self.would_exits:
                raise InvalidWorkFlowScript(f"The give source doesn't exist at action {action_data.get("id")}")
            from_state_space = True

        if from_state_space:
            remove_virtual_path : list[Path] = []

            for virtual_paths in self.would_exits:
                if FileSafety.is_relative_to(path1=path.resolve(), path2=virtual_paths.resolve()):
                    remove_virtual_path.append(virtual_paths.resolve())

            for paths_removed in remove_virtual_path:
                self.would_exits.discard(paths_removed.resolve())
                self.would_removed.add(paths_removed.resolve())
        else:
            self.would_removed.add(path.resolve())
            self.would_exits.discard(path.resolve())
            for paths in path.rglob("*"):
                self.would_exits.discard(paths.resolve())
                self.would_removed.add(paths.resolve())


    def validate_sequence_operation(self):
        for action_data in self.workflow_data["actions"]:
            match action_data.get("operation"):
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
                    raise InvalidWorkFlowScript(f"Invalid operation for action {action_data.get("id")}")

    def validate_workspace_scope(self, workspace : Path, path : Path, inside : bool = True):
        """checks if the action path is outside the workspace. to prevent operations outside of workspace"""
        if not FileSafety.is_relative_to(path1=workspace, path2=path):
            raise OutOfScope("Path is outside the configured workspace. Choose a path inside the workspace or change --workspace.")
        if inside:
            if FileSafety.same_path(path1=workspace, path2=path):
                raise WorkspaceProtection("This operation cannot target the workspace root itself. Choose an item inside the workspace.")
