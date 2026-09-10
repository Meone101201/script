"""
Streaming RBXLX XML Parser and Instance Tree Builder.
Processes place files of arbitrary size with low memory usage and full error tolerance.
"""

import os
import time
from typing import BinaryIO, Dict, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET

from ..model.instance import RobloxInstance
from ..utils.logger import ExtractorLogger
from .property_parser import PropertyParser, decode_attributes_binary, decode_tags_binary
from .stream_sanitizer import CleanReader


class RbxlxParser:
    def __init__(self, logger: ExtractorLogger):
        self.logger = logger
        self.shared_strings: Dict[str, str] = {}
        self.instances_by_referent: Dict[str, RobloxInstance] = {}
        self.root_services: List[RobloxInstance] = []
        self.total_instances_parsed = 0
        self.total_properties_parsed = 0

    def parse_file(
        self, file_path: str, filter_services: Optional[Set[str]] = None
    ) -> Tuple[RobloxInstance, Dict[str, RobloxInstance]]:
        """
        Parses an RBXLX file and constructs the Roblox Instance tree.
        Returns the synthetic DataModel root instance and the referent lookup table.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Place file not found: {file_path}")

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        self.logger.info(f"Opening '{file_path}' ({file_size_mb:.1f} MB)...", prefix="PARSER")

        # Create synthetic root DataModel
        data_model = RobloxInstance(class_name="DataModel", referent="DATAMODEL", name="DataModel")

        # Step 1: Pre-scan SharedStrings if present
        self._scan_shared_strings(file_path)

        prop_parser = PropertyParser(logger=self.logger, shared_strings=self.shared_strings)

        t0 = time.time()
        # Instance stack: items currently being parsed
        # Each entry is a RobloxInstance
        stack: List[RobloxInstance] = []

        with open(file_path, "rb") as raw_f:
            reader = CleanReader(raw_f)
            # Pull-parse events
            for event, elem in ET.iterparse(reader, events=("start", "end")):
                if event == "start":
                    if elem.tag == "Item":
                        cls_name = elem.attrib.get("class", "UnknownClass")
                        referent = elem.attrib.get("referent", f"REF_{self.total_instances_parsed}")
                        inst = RobloxInstance(class_name=cls_name, referent=referent)
                        stack.append(inst)

                elif event == "end":
                    if elem.tag == "Properties":
                        if stack:
                            curr_inst = stack[-1]
                            for p_elem in elem:
                                prop = prop_parser.parse_property(
                                    p_elem, instance_path=curr_inst.get_full_path()
                                )
                                if prop:
                                    curr_inst.properties[prop.name] = prop
                                    self.total_properties_parsed += 1

                                    if prop.name == "Name" and isinstance(prop.value, str) and prop.value:
                                        curr_inst.name = prop.value

                                    # Check for Tags
                                    if prop.name == "Tags" and isinstance(prop.value, str):
                                        curr_inst.tags = decode_tags_binary(prop.value)

                                    # Check for Attributes
                                    if prop.name == "AttributesSerialize" and isinstance(prop.value, str):
                                        curr_inst.attributes = decode_attributes_binary(prop.value)

                        # Clear properties XML element to free memory immediately
                        elem.clear()

                    elif elem.tag == "Item":
                        if stack:
                            inst = stack.pop()
                            self.total_instances_parsed += 1
                            self.instances_by_referent[inst.referent] = inst

                            if stack:
                                # Child instance
                                parent = stack[-1]
                                parent.add_child(inst)
                            else:
                                # Top-level Service instance
                                if not filter_services or inst.name in filter_services or inst.class_name in filter_services:
                                    data_model.add_child(inst)
                                    self.root_services.append(inst)

                        elem.clear()

        t_elapsed = time.time() - t0
        self.logger.info(
            f"Successfully parsed {self.total_instances_parsed} instances and "
            f"{self.total_properties_parsed} properties in {t_elapsed:.2f}s",
            prefix="PARSER"
        )
        self.logger.stats["totalInstances"] = self.total_instances_parsed
        self.logger.stats["totalProperties"] = self.total_properties_parsed

        return data_model, self.instances_by_referent

    def _scan_shared_strings(self, file_path: str) -> None:
        """Quickly scans SharedStrings from the start of the file if present."""
        try:
            with open(file_path, "rb") as f:
                # SharedStrings is usually near the top of the file
                header_bytes = f.read(512 * 1024)
                if b"<SharedStrings>" in header_bytes:
                    # Parse shared strings
                    idx_start = header_bytes.find(b"<SharedStrings>")
                    idx_end = header_bytes.find(b"</SharedStrings>")
                    if idx_start != -1 and idx_end != -1:
                        chunk = header_bytes[idx_start:idx_end + len(b"</SharedStrings>")]
                        root = ET.fromstring(chunk)
                        for ss in root.findall("SharedString"):
                            md5 = ss.attrib.get("md5", "")
                            val = ss.text or ""
                            if md5:
                                self.shared_strings[md5] = val
        except Exception as ex:
            self.logger.debug(f"SharedStrings pre-scan skipped: {ex}")
