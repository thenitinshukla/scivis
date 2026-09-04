from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET


def _set_value(node, key, value):
    node.set(key, str(value))


def save_xml_session(path: str | Path, state: dict):
    root = ET.Element("scientific_visualization_session", version="1")
    def encode(parent, name, obj):
        node = ET.SubElement(parent, name)
        if isinstance(obj, dict):
            node.set("type", "dict")
            for k, v in obj.items():
                encode(node, str(k), v)
        elif isinstance(obj, (list, tuple)):
            node.set("type", "list")
            for v in obj:
                encode(node, "item", v)
        else:
            node.set("type", "value")
            node.text = "" if obj is None else str(obj)
        return node
    encode(root, "state", state)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(str(path), encoding="utf-8", xml_declaration=True)
    return str(path)


def load_xml_session(path: str | Path) -> dict:
    root = ET.parse(str(path)).getroot()
    if root.tag != "scientific_visualization_session":
        raise ValueError("Not a Scientific Visualization session file")
    state = root.find("state")
    if state is None:
        raise ValueError("Session file contains no state")

    def decode(node):
        kind = node.get("type")
        if kind == "value":
            return node.text or ""
        if kind == "list":
            return [decode(child) for child in node.findall("item")]
        if kind == "dict":
            return {child.tag: decode(child) for child in node}
        raise ValueError(f"Unknown session value type: {kind!r}")

    return decode(state)


def value_as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def value_as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def value_as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
