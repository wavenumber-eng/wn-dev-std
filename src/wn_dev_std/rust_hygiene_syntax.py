"""Small Tree-sitter Rust syntax classification helpers."""

from __future__ import annotations

from tree_sitter import Node


def is_test_attribute(node: Node, source: bytes) -> bool:
    """Return whether an attribute directly marks test-only code."""
    attribute = next(iter(node.named_children), None)
    if attribute is None or not attribute.named_children:
        return False
    children = attribute.named_children
    name = node_text(children[0], source)
    if name == "test":
        return len(children) == 1
    if name.endswith("::test"):
        return True
    arguments = attribute.child_by_field_name("arguments")
    return name == "cfg" and node_text(arguments, source).replace(" ", "") == "(test)"


def node_text(node: Node | None, source: bytes) -> str:
    """Decode a Tree-sitter node's source span."""
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
