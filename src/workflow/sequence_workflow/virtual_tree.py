from __future__ import annotations
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel
from typing import Literal

from rich.tree import Tree

from workflow.exceptions import VirtualAlreadyExists, VirtualCollisionError, VirtualDestinationNotExists, VirtualInvalidItemType, VirtualNameInvalid, VirtualOperationOnSelf, VirtualParentAbsent, VirtualPathNotExists, VirtualRenameAlreadyExists, VirtualRootProtection, VirtualSourceNotExists, VirtualSuffixMissMatch, VirtualTypeCollision
from workflow.safety import FileSafety


"""
Note : 
1. Had to downgrade the flexibility to reduce complexity of the current MVP by only supporting Windows
2. Not optimized for efficiency


"""



def to_rich_tree(node: Node) -> Tree:
    icon = "📁" if node.type == "folder" else "📄"
    tree = Tree(f"{icon} {node.name}")

    for child in node.child.values():
        tree.add(to_rich_tree(child))

    return tree


class Node(BaseModel):
    name : str
    type : Literal["file", "folder"]
    parent : Node | None   
    child : dict[str, Node] = dict()    


class VirtualTree:
    def __init__(self, root_name : str) -> None:
        self.root_node = Node(name=root_name, type="folder", parent=None)

    def _normalize_relative_path(self, relative_path : Sequence[str]) -> tuple[str, ...]:
        return tuple(item.lower() for item in relative_path)

    def add_path(self, relative_path : Sequence[str], end_type : Literal["file", "folder"], recursive : bool = False, force : bool = False) -> bool:
        self._validate_not_root(relative_path)

        relative_path = self._normalize_relative_path(relative_path=relative_path)

        for node_name in relative_path:
            self.validate_name(node_name)

        force_create_raised = False

        if self.path_exists(relative_path=relative_path):
            
            if not force:
                raise VirtualAlreadyExists("The given path already exists")
            else:
                force_create_raised = True

        current_node = self.root_node
        tmp_node : Node | None
        for index, node_name in enumerate(relative_path):
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                is_target = (index == (len(relative_path) - 1))
                if is_target or recursive:
                    if current_node.type == "file":
                        raise VirtualInvalidItemType("Can't create a item inside a file")
                    current_node.child.setdefault(node_name, Node(name=node_name, type="folder", parent=current_node))
                    tmp_node = current_node.child.get(node_name)
                    if tmp_node is not None:
                        current_node = tmp_node
                else:
                    raise VirtualParentAbsent("Parent for the given path doesn't exists in virtual space")
            else:
                current_node = tmp_node
        if force_create_raised and current_node.type != end_type:
            raise VirtualTypeCollision("The given type overwrites the original type")
        else:
            current_node.type = end_type
        return True

    def remove_path(self, relative_path : Sequence[str]) -> bool:
        self._validate_not_root(relative_path)

        relative_path = self._normalize_relative_path(relative_path=relative_path)


        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                raise VirtualPathNotExists("The given path to remove doesn't exist in this virtual space")
            current_node = tmp_node

        parent = current_node.parent
        if parent is not None:
            parent.child.pop(current_node.name)
            return True
        else:
            return False

    def copy_path(self, relative_source_path : Sequence[str], relative_destination_path : Sequence[str]):
        self._validate_not_root(relative_source_path)

        relative_source_path = self._normalize_relative_path(relative_path=relative_source_path)
        relative_destination_path = self._normalize_relative_path(relative_path=relative_destination_path)

        
        source_node = self.root_node
        tmp_source_node : Node | None
        for source_node_name in relative_source_path:
            tmp_source_node = source_node.child.get(source_node_name)
            if tmp_source_node is None:
                raise VirtualSourceNotExists("The give source path doesn't exists")
            source_node = tmp_source_node

        destination_node = self.root_node
        tmp_destination_node : Node | None
        for destination_node_name in relative_destination_path:
            tmp_destination_node = destination_node.child.get(destination_node_name)
            if tmp_destination_node is None:
                raise VirtualDestinationNotExists("The give destination path doesn't exists")
            destination_node = tmp_destination_node


        if source_node.name in destination_node.child:
            raise VirtualCollisionError("The destination contains same item name as source")

        if destination_node.type == "file":
            raise VirtualInvalidItemType("Can't copy to a file")
        
        self.validate_pointing_inside(relative_source_path, relative_destination_path)

        source_copy = self.node_copy(source_node, destination_node)
        destination_node.child.setdefault(source_copy.name, source_copy)

    def node_copy(self, node : Node, parent : Node):
        new_node = Node(name=node.name, type=node.type, parent=parent)

        for child in node.child.values():
            clone_child = self.node_copy(child, new_node)
            new_node.child.setdefault(clone_child.name, clone_child)

        return new_node
        
    def move_path(self, relative_source_path : Sequence[str], relative_destination_path : Sequence[str]):
        self._validate_not_root(relative_source_path)

        relative_source_path = self._normalize_relative_path(relative_path=relative_source_path)
        relative_destination_path = self._normalize_relative_path(relative_path=relative_destination_path)

        source_node = self.root_node
        tmp_source_node : Node | None
        for source_node_name in relative_source_path:
            tmp_source_node = source_node.child.get(source_node_name)
            if tmp_source_node is None:
                raise VirtualSourceNotExists("The give source path doesn't exists")
            source_node = tmp_source_node

        destination_node = self.root_node
        tmp_destination_node : Node | None
        for destination_node_name in relative_destination_path:
            tmp_destination_node = destination_node.child.get(destination_node_name)
            if tmp_destination_node is None:
                raise VirtualDestinationNotExists("The give destination path doesn't exists")
            destination_node = tmp_destination_node


        if source_node.name in destination_node.child:
            raise VirtualCollisionError("The destination contains same item name as source")

        if destination_node.type == "file":
            raise VirtualInvalidItemType("Can't move to a file")

        self.validate_pointing_inside(relative_source_path, relative_destination_path)


        source_parent = source_node.parent
        if source_parent is not None:
            source_parent.child.pop(source_node.name)
            source_node.parent = destination_node
            destination_node.child.setdefault(source_node.name, source_node)


    def validate_pointing_inside(self, relative_source_path : Sequence[str], relative_destination_path : Sequence[str]):
        if len(relative_destination_path) >= len(relative_source_path)  and  relative_destination_path[:len(relative_source_path)] == relative_source_path:
            raise VirtualOperationOnSelf("Operation on itself is invalid") 


    def validate_name(self, name : str):
        if not FileSafety.check_if_valid_name(name=name):
            raise VirtualNameInvalid("The given name is invalid")

    def validate_extension(self, original_name : str, new_name : str):
        if Path(original_name).suffix != Path(new_name).suffix:
            raise VirtualSuffixMissMatch("The give new name overwrites the extension. use --force to allow overwrites")

    def _get_unique_name(self, new_relative_path: list[str], type : Literal["file", "folder"]) -> str:
        tmp_name = Path(new_relative_path[-1])
        stem = tmp_name.stem if type == "file" else tmp_name.name
        suffix = tmp_name.suffix if type == "file" else ""
        number = 2
        while True:
            new_relative_path[-1] = f"{stem}{number}{suffix}"
            if not self.path_exists(new_relative_path):
                return new_relative_path[-1]
            number += 1

    def rename_path_node(self, relative_path : Sequence[str], new_name : str, force : bool = False) -> bool:
        self._validate_not_root(relative_path)

        relative_path = self._normalize_relative_path(relative_path=relative_path)

        new_name = new_name.lower()

        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                raise VirtualPathNotExists("The given path doesn't exist in this virtual space")
            current_node = tmp_node

        self.validate_name(name=new_name)
        
        if current_node.name == new_name:
            raise VirtualOperationOnSelf("The new name is the same as the current name")

        if not force and current_node.type == "file":
            self.validate_extension(original_name=current_node.name, new_name=new_name) 
    
        parent = current_node.parent

        if parent is not None:
            if new_name in parent.child:
                if force:
                    tmp_relative_path = list(relative_path)
                    tmp_relative_path[-1] = new_name
                    new_name = self._get_unique_name(new_relative_path=tmp_relative_path, type=current_node.type)
                else:
                    raise VirtualRenameAlreadyExists("The given new name already exists in that same directory")
            parent.child.pop(current_node.name)
            current_node.name = new_name
            parent.child.setdefault(new_name, current_node)
            return True
        return False
        

    def path_exists_and_type(self, relative_path : Sequence[str], type : Literal["file", "folder"]):
        relative_path = self._normalize_relative_path(relative_path=relative_path)
        
        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                return False
            current_node = tmp_node
        return current_node.type == type   

    def path_exists(self, relative_path : Sequence[str]):
        relative_path = self._normalize_relative_path(relative_path=relative_path)
        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                return False
            current_node = tmp_node
        return True

    def _validate_not_root(self, relative_path: Sequence[str]) -> None:
        if not relative_path:
            raise VirtualRootProtection("The virtual workspace root cannot be modified")
        
    
