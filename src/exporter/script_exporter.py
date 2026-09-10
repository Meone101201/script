"""
Script Exporter.
Extracts script source code to .server.lua, .client.lua, and .lua files.
Preserves exact source content and records metrics for manifest.
"""

from dataclasses import dataclass
import os
from typing import Any, Dict, List, Optional
from ..model.instance import RobloxInstance
from ..utils.logger import ExtractorLogger
from ..utils.sanitize import ensure_extended_path


@dataclass
class ExportedScriptInfo:
    referent: str
    class_name: str
    name: str
    roblox_path: str
    filesystem_path: str
    lines: int
    size_bytes: int

    def to_json(self) -> Dict[str, Any]:
        return {
            "referent": self.referent,
            "className": self.class_name,
            "name": self.name,
            "robloxPath": self.roblox_path,
            "filesystemPath": self.filesystem_path,
            "lines": self.lines,
            "sizeBytes": self.size_bytes,
        }


class ScriptExporter:
    def __init__(self, logger: ExtractorLogger):
        self.logger = logger
        self.exported_scripts: List[ExportedScriptInfo] = []

    def export_script(
        self,
        instance: RobloxInstance,
        target_file_path: str,
        relative_path: str,
    ) -> ExportedScriptInfo:
        """
        Writes script source to the target filesystem path.
        """
        source = instance.get_script_source()
        if source is None:
            source = ""

        extended_path = ensure_extended_path(target_file_path)
        os.makedirs(os.path.dirname(extended_path), exist_ok=True)

        # Write verbatim UTF-8 source without altering newlines or indent
        with open(extended_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(source)

        line_count = source.count("\n") + (1 if source else 0)
        size_bytes = len(source.encode("utf-8"))

        info = ExportedScriptInfo(
            referent=instance.referent,
            class_name=instance.class_name,
            name=instance.name,
            roblox_path=instance.get_full_path(),
            filesystem_path=relative_path.replace("\\", "/"),
            lines=line_count,
            size_bytes=size_bytes,
        )
        self.exported_scripts.append(info)

        # Update stats
        st = instance.get_script_type()
        self.logger.stats["totalScripts"] += 1
        if st == "server":
            self.logger.stats["serverScripts"] += 1
        elif st == "client":
            self.logger.stats["localScripts"] += 1
        elif st == "module":
            self.logger.stats["moduleScripts"] += 1

        return info
