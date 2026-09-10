"""
Manifest Exporter.
Generates manifest.json describing project metadata, statistics, scripts, and warnings.
"""

from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, List, Optional
from ..utils.logger import ExtractorLogger
from .script_exporter import ExportedScriptInfo


class ManifestExporter:
    def __init__(self, logger: ExtractorLogger, pretty: bool = True):
        self.logger = logger
        self.pretty = pretty

    def export_manifest(
        self,
        source_file: str,
        output_dir: str,
        services: List[str],
        scripts: List[ExportedScriptInfo],
        instances_summary: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Writes manifest.json to the output directory.
        Returns the path to manifest.json.
        """
        os.makedirs(output_dir, exist_ok=True)
        manifest_path = os.path.join(output_dir, "manifest.json")

        source_name = os.path.basename(source_file)
        source_size = os.path.getsize(source_file) if os.path.isfile(source_file) else 0

        manifest_data: Dict[str, Any] = {
            "format": "rbxlx-export",
            "version": 1,
            "source": {
                "file": source_name,
                "sizeBytes": source_size,
            },
            "exportTimestamp": datetime.now(timezone.utc).isoformat(),
            "stats": self.logger.stats,
            "services": sorted(services),
            "scripts": [s.to_json() for s in scripts],
            "warningsSummary": {
                "total": len(self.logger.warnings),
                "byCategory": self.logger.category_counts,
            },
        }

        if instances_summary is not None:
            manifest_data["instances"] = instances_summary

        with open(manifest_path, "w", encoding="utf-8") as f:
            if self.pretty:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(manifest_data, f, separators=(",", ":"), ensure_ascii=False)

        return manifest_path
