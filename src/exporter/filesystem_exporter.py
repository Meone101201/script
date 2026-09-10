"""
Filesystem Exporter.
Translates Roblox Instance Tree into nested directories and files on disk.
Handles sibling collisions, long paths, script separation, and metadata files.
"""

import os
from typing import Any, Dict, List, Optional, Set
from ..model.instance import RobloxInstance
from ..utils.logger import ExtractorLogger
from ..utils.sanitize import SiblingCollisionResolver, ensure_extended_path
from .metadata_exporter import MetadataExporter
from .script_exporter import ExportedScriptInfo, ScriptExporter


class FilesystemExporter:
    def __init__(
        self,
        logger: ExtractorLogger,
        output_dir: str,
        extract_scripts: bool = True,
        include_properties: bool = True,
        pretty: bool = False,
        rojo_style: bool = False,
    ):
        self.logger = logger
        self.output_dir = os.path.abspath(output_dir)
        self.extract_scripts = extract_scripts
        self.include_properties = include_properties
        self.pretty = pretty
        self.rojo_style = rojo_style

        self.script_exporter = ScriptExporter(logger=self.logger)
        self.metadata_exporter = MetadataExporter(
            logger=self.logger, pretty=self.pretty, include_properties=self.include_properties
        )
        self.exported_instances_summary: List[Dict[str, Any]] = []

    def export_tree(self, root: RobloxInstance) -> List[ExportedScriptInfo]:
        """
        Exports the entire Roblox Instance tree to the filesystem.
        Root is assumed to be DataModel whose direct children are Roblox Services.
        """
        self.logger.info(f"Exporting Roblox Instance Tree to '{self.output_dir}'...", prefix="EXPORTER")
        os.makedirs(self.output_dir, exist_ok=True)

        service_collision_resolver = SiblingCollisionResolver()

        for service in root.children:
            service_fs_name = service_collision_resolver.get_unique_name(service.name)
            service.filesystem_name = service_fs_name
            service_dir = os.path.join(self.output_dir, service_fs_name)
            service.filesystem_path = service_dir

            # Export service metadata
            self.metadata_exporter.export_metadata(service, service_dir)
            self._record_instance_summary(service, service_dir)

            # Export service children
            self._export_children(service, service_dir)

        self.logger.info(
            f"Export completed: {self.logger.stats['totalScripts']} scripts exported, "
            f"{len(self.exported_instances_summary)} instances recorded.",
            prefix="EXPORTER"
        )
        return self.script_exporter.exported_scripts

    def _export_children(self, parent: RobloxInstance, parent_dir: str) -> None:
        collision_resolver = SiblingCollisionResolver()

        for child in parent.children:
            is_script = child.is_script() and self.extract_scripts
            has_children = len(child.children) > 0

            if is_script and not has_children:
                # Script without children: export directly as a script file
                ext = child.get_script_extension()
                unique_file_name = collision_resolver.get_unique_name(child.name, extension=ext)
                child.filesystem_name = unique_file_name
                file_path = os.path.join(parent_dir, unique_file_name)
                child.filesystem_path = file_path

                rel_path = os.path.relpath(file_path, self.output_dir)
                self.script_exporter.export_script(child, file_path, rel_path)
                self._record_instance_summary(child, file_path)

            elif is_script and has_children:
                # Script with children: create folder for script
                folder_name = collision_resolver.get_unique_name(child.name)
                child.filesystem_name = folder_name
                script_dir = os.path.join(parent_dir, folder_name)
                child.filesystem_path = script_dir
                os.makedirs(ensure_extended_path(script_dir), exist_ok=True)

                # Script source file inside folder
                ext = child.get_script_extension()
                if self.rojo_style:
                    # init.server.lua style
                    script_file_name = f"init{ext}"
                else:
                    # <ScriptName>.server.lua style
                    script_file_name = f"{folder_name}{ext}"

                script_file_path = os.path.join(script_dir, script_file_name)
                rel_path = os.path.relpath(script_file_path, self.output_dir)
                self.script_exporter.export_script(child, script_file_path, rel_path)

                # Export metadata for the script instance
                self.metadata_exporter.export_metadata(child, script_dir)
                self._record_instance_summary(child, script_dir)

                # Export its child instances
                self._export_children(child, script_dir)

            else:
                # Non-script instance (Part, Model, Folder, Value, Gui, etc.)
                folder_name = collision_resolver.get_unique_name(child.name)
                child.filesystem_name = folder_name
                inst_dir = os.path.join(parent_dir, folder_name)
                child.filesystem_path = inst_dir
                os.makedirs(ensure_extended_path(inst_dir), exist_ok=True)

                # Export instance.json
                self.metadata_exporter.export_metadata(child, inst_dir)
                self._record_instance_summary(child, inst_dir)

                # Export its child instances
                if has_children:
                    self._export_children(child, inst_dir)

    def _record_instance_summary(self, instance: RobloxInstance, full_fs_path: str) -> None:
        rel_path = os.path.relpath(full_fs_path, self.output_dir).replace("\\", "/")
        self.exported_instances_summary.append({
            "referent": instance.referent,
            "className": instance.class_name,
            "name": instance.name,
            "path": instance.get_full_path(),
            "filesystemPath": rel_path,
        })
