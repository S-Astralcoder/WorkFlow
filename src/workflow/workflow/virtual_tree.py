from pydantic import BaseModel
from typing import Literal


class Node(BaseModel):
    name : str
    type : Literal["file", "folder"]
    parent : Node | None   # pyright: ignore[reportUndefinedVariable]
    child : dict[str, Node] | None  # pyright: ignore[reportUndefinedVariable]



class VirtualTree:
    def __init__(self, root_name : str) -> None:
        self.root_node = Node(name=root_name, type="folder", child=None, parent=None)

    

    