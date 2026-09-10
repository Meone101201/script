"""
Tests for RbxlxParser: empty place, simple part, and nested hierarchy.
"""

from src.parser.rbxlx_parser import RbxlxParser
from src.utils.logger import ExtractorLogger


def test_parse_empty_place(get_fixture_path):
    logger = ExtractorLogger()
    parser = RbxlxParser(logger=logger)
    file_path = get_fixture_path("empty_place.rbxlx")

    data_model, ref_map = parser.parse_file(file_path)

    assert data_model.class_name == "DataModel"
    assert len(data_model.children) == 2

    # Verify top-level services
    service_names = [c.name for c in data_model.children]
    assert "Workspace" in service_names
    assert "Lighting" in service_names

    assert "RBX_WS" in ref_map
    assert "RBX_LIGHT" in ref_map


def test_parse_simple_part(get_fixture_path):
    logger = ExtractorLogger()
    parser = RbxlxParser(logger=logger)
    file_path = get_fixture_path("simple_part.rbxlx")

    data_model, ref_map = parser.parse_file(file_path)

    assert "RBX_PART1" in ref_map
    part = ref_map["RBX_PART1"]

    assert part.class_name == "Part"
    assert part.name == "BasePlate"
    assert part.parent is not None
    assert part.parent.name == "Workspace"

    # Verify properties
    assert part.properties["Anchored"].value is True
    assert part.properties["CanCollide"].value is True
    assert part.properties["Transparency"].value == 0.0

    size = part.properties["Size"].value
    assert size.x == 512.0
    assert size.y == 20.0
    assert size.z == 512.0

    color = part.properties["Color"].value
    assert round(color.r, 4) == 0.3882


def test_parse_nested_model(get_fixture_path):
    logger = ExtractorLogger()
    parser = RbxlxParser(logger=logger)
    file_path = get_fixture_path("nested_model.rbxlx")

    data_model, ref_map = parser.parse_file(file_path)

    door = ref_map["RBX_DOOR"]
    window = ref_map["RBX_WINDOW"]
    house = ref_map["RBX_HOUSE"]
    map_folder = ref_map["RBX_MAP"]

    assert door.parent == house
    assert window.parent == house
    assert house.parent == map_folder
    assert map_folder.parent.name == "Workspace"

    assert door.get_full_path() == "Workspace.Map.House.Door"
    assert window.get_full_path() == "Workspace.Map.House.Window"
