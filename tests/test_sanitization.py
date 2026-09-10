"""
Tests for filename sanitization and sibling collision resolution.
"""

from src.utils.sanitize import (
    sanitize_filesystem_name,
    SiblingCollisionResolver,
    ensure_extended_path,
)


def test_sanitize_basic():
    assert sanitize_filesystem_name("SimplePart") == "SimplePart"
    assert sanitize_filesystem_name("Map_Folder-123") == "Map_Folder-123"


def test_sanitize_invalid_characters():
    assert sanitize_filesystem_name("Door:Front/Left*1?2\"3<4>5|6") == "Door_Front_Left_1_2_3_4_5_6"
    assert sanitize_filesystem_name("Hello\x00World\x1fTest") == "Hello_World_Test"


def test_sanitize_reserved_windows_names():
    assert sanitize_filesystem_name("CON") == "_CON"
    assert sanitize_filesystem_name("con") == "_con"
    assert sanitize_filesystem_name("NUL") == "_NUL"
    assert sanitize_filesystem_name("AUX") == "_AUX"
    assert sanitize_filesystem_name("COM1") == "_COM1"
    assert sanitize_filesystem_name("LPT9") == "_LPT9"
    assert sanitize_filesystem_name("CON.lua") == "_CON.lua"


def test_sanitize_trailing_spaces_and_dots():
    assert sanitize_filesystem_name("Spacing Test...   ") == "Spacing Test"
    assert sanitize_filesystem_name("...Folder...") == "Folder"
    assert sanitize_filesystem_name("   ") == "Unnamed"
    assert sanitize_filesystem_name("") == "Unnamed"
    assert sanitize_filesystem_name(None) == "Unnamed"


def test_sibling_collision_resolver():
    resolver = SiblingCollisionResolver(case_insensitive=True)

    # First instance
    assert resolver.get_unique_name("Part") == "Part"
    # Second instance with same name
    assert resolver.get_unique_name("Part") == "Part_2"
    # Third instance
    assert resolver.get_unique_name("Part") == "Part_3"
    # Case insensitivity test
    assert resolver.get_unique_name("part") == "part_4"
    # Different name
    assert resolver.get_unique_name("Model") == "Model"


def test_sibling_collision_with_extensions():
    resolver = SiblingCollisionResolver(case_insensitive=True)

    assert resolver.get_unique_name("Main", extension=".server.lua") == "Main.server.lua"
    assert resolver.get_unique_name("Main", extension=".server.lua") == "Main_2.server.lua"
    assert resolver.get_unique_name("Main", extension=".server.lua") == "Main_3.server.lua"


def test_ensure_extended_path():
    short_path = "C:\\Windows\\test"
    ext_path = ensure_extended_path(short_path)
    # On Windows, should have \\?\ prefix
    import os
    if os.name == "nt":
        assert ext_path.startswith("\\\\?\\")
