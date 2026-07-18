from __future__ import annotations

from pydantic import BaseModel
from typing import Literal



from rich.tree import Tree

from workflow.exceptions import VirtualAlreadyExists, VirtualCollisionError, VirtualDestinationNotExists, VirtualInvalidItemType, VirtualOperationOnSelf, VirtualParentAbsent, VirtualPathNotExists, VirtualRenameAlreadyExists, VirtualRootProtection, VirtualSourceNotExists

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

    def add_path(self, relative_path : list[str], end_type : Literal["file", "folder"], recursive : bool = False) -> bool:
        self._validate_not_root(relative_path)
        if self.path_exists(relative_path=relative_path):
            raise VirtualAlreadyExists("The given path already exists")
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
        current_node.type = end_type
        return True

    def remove_path(self, relative_path : list[str]) -> bool:
        self._validate_not_root(relative_path)
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


    def copy_path(self, relative_source_path : list[str], relative_destination_path : list[str]):
        self._validate_not_root(relative_source_path)
        self.validate_pointing_inside(relative_source_path, relative_destination_path)
        
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

        source_copy = self.node_copy(source_node, destination_node)
        destination_node.child.setdefault(source_copy.name, source_copy)

    def node_copy(self, node : Node, parent : Node):
        new_node = Node(name=node.name, type=node.type, parent=parent)

        for child in node.child.values():
            clone_child = self.node_copy(child, new_node)
            new_node.child.setdefault(clone_child.name, clone_child)

        return new_node
        
    def move_path(self, relative_source_path : list[str], relative_destination_path : list[str]):
        self._validate_not_root(relative_source_path)
        self.validate_pointing_inside(relative_source_path, relative_destination_path)
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
        
        source_parent = source_node.parent
        if source_parent is not None:
            source_parent.child.pop(source_node.name)
            source_node.parent = destination_node
            destination_node.child.setdefault(source_node.name, source_node)


    def validate_pointing_inside(self, relative_source_path : list[str], relative_destination_path : list[str]):
        if len(relative_destination_path) >= len(relative_source_path)  and  relative_destination_path[:len(relative_source_path)] == relative_source_path:
            raise VirtualOperationOnSelf("Operation on itself is invalid") 

    def rename_path_node(self, relative_path : list[str], new_name : str) -> bool:
        self._validate_not_root(relative_path)
        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                raise VirtualPathNotExists("The given path doesn't exist in this virtual space")
            current_node = tmp_node

        parent = current_node.parent

        if parent is not None:
            if new_name in parent.child:
                raise VirtualRenameAlreadyExists("The given new name already exists in that same directory")
            else:
                parent.child.pop(current_node.name)
                current_node.name = new_name
                parent.child.setdefault(new_name, current_node)
                return True
        return False
        

    def path_exists_and_type(self, relative_path : list[str], type : Literal["file", "folder"]):
        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                return False
            current_node = tmp_node
        return current_node.type == type   

    def path_exists(self, relative_path : list[str]):
        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                return False
            current_node = tmp_node
        return True

    def _validate_not_root(self, relative_path: list[str]) -> None:
        if not relative_path:
            raise VirtualRootProtection("The virtual workspace root cannot be modified")
        
    
