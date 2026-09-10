"""
Tests for special cases: duplicate names, special characters, and unknown classes/properties.
"""

import json
import os
import shutil
import tempfile
from src.main import run_pipeline


def test_duplicate_names_export(get_fixture_path):
    temp_out = tempfile.mkdtemp(prefix="rbx_test_dup_")
    try:
        fixture_path = get_fixture_path("duplicate_names.rbxlx")
        exit_code = run_pipeline(input_file=fixture_path, output_dir=temp_out)
        assert exit_code == 0

        ws_dir = os.path.join(temp_out, "Workspace")

        # Parts should be Part, Part_2, Part_3
        p1 = os.path.join(ws_dir, "Part")
        p2 = os.path.join(ws_dir, "Part_2")
        p3 = os.path.join(ws_dir, "Part_3")

        assert os.path.isdir(p1)
        assert os.path.isdir(p2)
        assert os.path.isdir(p3)

        # Scripts should be Handler.server.lua, Handler_2.server.lua
        s1 = os.path.join(ws_dir, "Handler.server.lua")
        s2 = os.path.join(ws_dir, "Handler_2.server.lua")

        assert os.path.isfile(s1)
        assert os.path.isfile(s2)

        # Verify metadata still has original name "Part"
        with open(os.path.join(p2, "instance.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["name"] == "Part"
            assert data["filesystemName"] == "Part_2"

    finally:
        shutil.rmtree(temp_out, ignore_errors=True)


def test_special_characters_export(get_fixture_path):
    temp_out = tempfile.mkdtemp(prefix="rbx_test_spec_")
    try:
        fixture_path = get_fixture_path("special_characters.rbxlx")
        exit_code = run_pipeline(input_file=fixture_path, output_dir=temp_out)
        assert exit_code == 0

        ws_dir = os.path.join(temp_out, "Workspace")

        # CON and NUL should be prefixed with underscore on Windows
        con_dir = os.path.join(ws_dir, "_CON")
        nul_dir = os.path.join(ws_dir, "_NUL")
        assert os.path.isdir(con_dir)
        assert os.path.isdir(nul_dir)

        # Sanitized name: Door:Front/Left*1?2"3<4>5|6 -> Door_Front_Left_1_2_3_4_5_6
        spec_dir = os.path.join(ws_dir, "Door_Front_Left_1_2_3_4_5_6")
        assert os.path.isdir(spec_dir)

        # Trailing dots and spaces stripped: Spacing Test...   -> Spacing Test
        trail_dir = os.path.join(ws_dir, "Spacing Test")
        assert os.path.isdir(trail_dir)

    finally:
        shutil.rmtree(temp_out, ignore_errors=True)


def test_unknown_class_and_property(get_fixture_path):
    temp_out = tempfile.mkdtemp(prefix="rbx_test_unk_")
    try:
        fixture_path = get_fixture_path("unknown_and_broken.rbxlx")
        exit_code = run_pipeline(input_file=fixture_path, output_dir=temp_out)
        assert exit_code == 0

        ws_dir = os.path.join(temp_out, "Workspace")
        gizmo_dir = os.path.join(ws_dir, "ExperimentalGizmo")
        assert os.path.isdir(gizmo_dir)

        # Check instance.json preserves raw property data
        with open(os.path.join(gizmo_dir, "instance.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["className"] == "FutureRobloxSuperEngine"
            assert "FluxDensity" in data["properties"]
            flux = data["properties"]["FluxDensity"]
            # Raw XML data preserved
            assert flux is not None

        # Check warnings.log has entries for unsupported datatype and broken reference
        with open(os.path.join(temp_out, "warnings.log"), "r", encoding="utf-8") as f:
            log_content = f.read()
            assert "UnsupportedDatatype" in log_content
            assert "BrokenReference" in log_content

    finally:
        shutil.rmtree(temp_out, ignore_errors=True)
