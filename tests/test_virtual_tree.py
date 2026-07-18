import pytest

from workflow.exceptions import VirtualRootProtection
from workflow.sequence_workflow.virtual_tree import VirtualTree


def test_create_rejects_virtual_root() -> None:
    tree = VirtualTree("workspace")

    with pytest.raises(VirtualRootProtection):
        tree.add_path([], "file")

    assert tree.root_node.type == "folder"


def test_delete_rejects_virtual_root() -> None:
    tree = VirtualTree("workspace")

    with pytest.raises(VirtualRootProtection):
        tree.remove_path([])


def test_copy_rejects_virtual_root_as_source() -> None:
    tree = VirtualTree("workspace")
    tree.add_path(["destination"], "folder")

    with pytest.raises(VirtualRootProtection):
        tree.copy_path([], ["destination"])


def test_move_rejects_virtual_root_as_source() -> None:
    tree = VirtualTree("workspace")
    tree.add_path(["destination"], "folder")

    with pytest.raises(VirtualRootProtection):
        tree.move_path([], ["destination"])


def test_rename_rejects_virtual_root() -> None:
    tree = VirtualTree("workspace")

    with pytest.raises(VirtualRootProtection):
        tree.rename_path_node([], "renamed")
