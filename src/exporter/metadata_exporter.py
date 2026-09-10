"""
Metadata Exporter.
Serializes instance.json for non-script instances (and scripts with children/properties).
"""

import json
import os
from typing import Any, Dict
from ..model.instance import RobloxInstance
from ..utils.logger import ExtractorLogger
from ..utils.sanitize import ensure_extended_path


class MetadataExporter:
    def __init__(self, logger: ExtractorLogger, pretty: bool = False, include_properties: bool = True):
        self.logger = logger
        self.pretty = pretty
        self.include_properties = include_properties

    def export_metadata(self, instance: RobloxInstance, target_dir_path: str) -> str:
        """
        Writes instance.json inside the target directory.
        Returns the path to the written file.
        """
        extended_dir = ensure_extended_path(target_dir_path)
        os.makedirs(extended_dir, exist_ok=True)
        file_path = os.path.join(extended_dir, "instance.json")

        meta = instance.to_metadata_dict(include_properties=self.include_properties)

        with open(file_path, "w", encoding="utf-8") as f:
            if self.pretty:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            else:
                json.dump(meta, f, separators=(",", ":"), ensure_ascii=False)

        return file_path
