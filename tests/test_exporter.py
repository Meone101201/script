"""
Tests for Filesystem, Script, Metadata, and Manifest Exporters.
"""

import json
import os
import shutil
import tempfile
from src.main import run_pipeline


def test_full_export_pipeline(get_fixture_path):
    temp_out = tempfile.mkdtemp(prefix="rbx_test_out_")
    try:
        fixture_path = get_fixture_path("script_types.rbxlx")

        exit_code = run_pipeline(
            input_file=fixture_path,
            output_dir=temp_out,
            pretty=True,
            include_properties=True,
            extract_scripts=True,
        )
        assert exit_code == 0

        # Check expected folder structure
        sss_dir = os.path.join(temp_out, "ServerScriptService")
        sp_dir = os.path.join(temp_out, "StarterPlayer")
        rs_dir = os.path.join(temp_out, "ReplicatedStorage")

        assert os.path.isdir(sss_dir)
        assert os.path.isdir(sp_dir)
        assert os.path.isdir(rs_dir)

        # 1. Server Script without children -> Main.server.lua directly
        main_script = os.path.join(sss_dir, "Main.server.lua")
        assert os.path.isfile(main_script)
        with open(main_script, "r", encoding="utf-8") as f:
            content = f.read()
            assert content == 'print("Server running")'

        # 2. Server Script with children -> GunManager/ folder with GunManager.server.lua + instance.json
        gun_manager_dir = os.path.join(sss_dir, "GunManager")
        assert os.path.isdir(gun_manager_dir)
        gun_script = os.path.join(gun_manager_dir, "GunManager.server.lua")
        assert os.path.isfile(gun_script)
        with open(gun_script, "r", encoding="utf-8") as f:
            assert f.read() == 'print("Gun manager active")'

        gun_meta = os.path.join(gun_manager_dir, "instance.json")
        assert os.path.isfile(gun_meta)

        # Check GunManager children: AmmoConfig (NumberValue) and ReloadEvent (RemoteEvent)
        ammo_dir = os.path.join(gun_manager_dir, "AmmoConfig")
        assert os.path.isdir(ammo_dir)
        ammo_meta = os.path.join(ammo_dir, "instance.json")
        assert os.path.isfile(ammo_meta)
        with open(ammo_meta, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["className"] == "NumberValue"
            assert data["properties"]["Value"] == 30.0

        # 3. Client Script -> ClientHandler.client.lua
        sps_dir = os.path.join(sp_dir, "StarterPlayerScripts")
        client_script = os.path.join(sps_dir, "ClientHandler.client.lua")
        assert os.path.isfile(client_script)
        with open(client_script, "r", encoding="utf-8") as f:
            assert f.read() == 'print("Client running")'

        # 4. Module Script -> MathUtils.lua
        modules_dir = os.path.join(rs_dir, "Modules")
        module_script = os.path.join(modules_dir, "MathUtils.lua")
        assert os.path.isfile(module_script)
        with open(module_script, "r", encoding="utf-8") as f:
            assert "function M.add(a, b)" in f.read()

        # 5. Manifest.json
        manifest_path = os.path.join(temp_out, "manifest.json")
        assert os.path.isfile(manifest_path)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            assert manifest["format"] == "rbxlx-export"
            assert manifest["version"] == 1
            assert manifest["stats"]["totalScripts"] == 4
            assert manifest["stats"]["serverScripts"] == 2
            assert manifest["stats"]["localScripts"] == 1
            assert manifest["stats"]["moduleScripts"] == 1
            assert len(manifest["scripts"]) == 4

        # 6. Warnings.log
        warnings_path = os.path.join(temp_out, "warnings.log")
        assert os.path.isfile(warnings_path)

    finally:
        shutil.rmtree(temp_out, ignore_errors=True)
