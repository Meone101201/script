"""
XML parsing helper utilities.
"""

from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET


def get_elem_text(elem: Optional[ET.Element], default: str = "") -> str:
    """Returns text inside an XML element, stripping None."""
    if elem is None or elem.text is None:
        return default
    return elem.text


def get_child_text(parent: ET.Element, tag: str, default: str = "") -> str:
    """Finds child element with tag and returns its text."""
    child = parent.find(tag)
    return get_elem_text(child, default)


def elem_to_dict(elem: ET.Element) -> Dict[str, Any]:
    """Converts an unknown XML element tree into a dictionary to preserve raw data."""
    data: Dict[str, Any] = {
        "tag": elem.tag,
        "attrib": dict(elem.attrib),
    }
    if elem.text and elem.text.strip():
        data["text"] = elem.text.strip()

    children = [elem_to_dict(c) for c in elem]
    if children:
        data["children"] = children

    return data
