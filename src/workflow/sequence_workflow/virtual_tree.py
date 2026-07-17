from __future__ import annotations

from pydantic import BaseModel
from typing import Literal



from rich.console import Console
from rich.tree import Tree

from workflow.exceptions import VirtualParentAbsent





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
        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                if relative_path[-1] == node_name or recursive:
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
        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                raise VirtualParentAbsent("The given path to remove doesn't exist in this virtual space")
            current_node = tmp_node

        parent = current_node.parent
        if parent is not None:
            parent.child.pop(current_node.name)
            return True
        else:
            return False


    def copy_path(self, relative_source_path : list[str], relative_destination_path : list[str]):
        pass


    def move_path(self, relative_source_path : list[str], relative_destination_path : list[str]):
        pass

    def rename_path_node(self, relative_path : list[str], new_name : str):
        current_node = self.root_node
        tmp_node : Node | None
        for node_name in relative_path:
            tmp_node = current_node.child.get(node_name)
            if tmp_node is None:
                raise VirtualParentAbsent("The given path doesn't exist in this virtual space")
            current_node = tmp_node
        current_node.name = new_name
        
    

virtual_tree = VirtualTree("base")

virtual_tree.add_path(["test", "my", "to.txt"], "file", recursive=True)
virtual_tree.add_path(["test", "my", "do.txt"], "file")
virtual_tree.add_path(["test", "my", "what.txt"], "file")

virtual_tree.add_path(["test", "self", "to.txt"], "file", recursive=True)
virtual_tree.add_path(["self", "my", "do.txt"], "file")
virtual_tree.add_path(["test", "self", "what.txt"], "file")
virtual_tree.add_path(["test", "self", "what", "todo", "oh", "text.txt"], "file")

print(virtual_tree.remove_path(["test", "my", "to.txtq"]))

Console().print(to_rich_tree(virtual_tree.root_node))
        
        
    