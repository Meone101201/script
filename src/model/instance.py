"""
Roblox Instance tree node and metadata representation.
"""

from typing import Any, Dict, List, Optional, Set
from .property import RobloxProperty

SCRIPT_CLASSES: Set[str] = {"Script", "LocalScript", "ModuleScript"}

ASSET_PROPERTY_NAMES: Set[str] = {
    "MeshId", "TextureID", "TextureId", "SoundId", "AnimationId",
    "Image", "Texture", "Video", "PackageId", "LinkedSource",
    "PantsTemplate", "ShirtTemplate", "Graphic"
}


class RobloxInstance:
    def __init__(self, class_name: str, referent: str, name: str = ""):
        self.class_name: str = class_name
        self.referent: str = referent
        self.name: str = name or class_name
        self.parent: Optional["RobloxInstance"] = None
        self.children: List["RobloxInstance"] = []
        self.properties: Dict[str, RobloxProperty] = {}
        self.attributes: Dict[str, Any] = {}
        self.tags: List[str] = []
        self.raw_properties: Dict[str, Any] = {}
        self.filesystem_name: Optional[str] = None
        self.filesystem_path: Optional[str] = None

    def add_child(self, child: "RobloxInstance") -> None:
        child.parent = self
        self.children.append(child)

    def is_script(self) -> bool:
        return self.class_name in SCRIPT_CLASSES

    def get_script_type(self) -> Optional[str]:
        if self.class_name == "Script":
            return "server"
        elif self.class_name == "LocalScript":
            return "client"
        elif self.class_name == "ModuleScript":
            return "module"
        return None

    def get_script_extension(self) -> str:
        st = self.get_script_type()
        if st == "server":
            return ".server.lua"
        elif st == "client":
            return ".client.lua"
        elif st == "module":
            return ".lua"
        return ""

    def get_script_source(self) -> Optional[str]:
        if "Source" in self.properties:
            val = self.properties["Source"].value
            if isinstance(val, str):
                return val
        return None

    def get_full_path(self) -> str:
        """Returns canonical Roblox hierarchy path (e.g. Workspace.Map.House.Door)."""
        parts = []
        curr: Optional[RobloxInstance] = self
        while curr is not None:
            if curr.class_name != "DataModel" and curr.name:
                parts.append(curr.name)
            curr = curr.parent
        return ".".join(reversed(parts))

    def get_asset_properties(self) -> Dict[str, str]:
        """Scans properties for Roblox asset URLs or IDs."""
        assets: Dict[str, str] = {}
        for prop_name, prop in self.properties.items():
            val = prop.value
            if isinstance(val, str):
                if prop_name in ASSET_PROPERTY_NAMES or any(
                    prefix in val for prefix in ("rbxassetid://", "rbxasset://", "http://", "https://")
                ):
                    assets[prop_name] = val
        return assets

    def to_metadata_dict(self, include_properties: bool = True) -> Dict[str, Any]:
        """Builds dictionary for instance.json."""
        data: Dict[str, Any] = {
            "className": self.class_name,
            "name": self.name,
            "referent": self.referent,
            "path": self.get_full_path(),
        }

        if self.filesystem_name:
            data["filesystemName"] = self.filesystem_name

        # UniqueId if present
        if "UniqueId" in self.properties:
            uid_val = self.properties["UniqueId"].value
            if uid_val:
                data["uniqueId"] = uid_val

        if self.tags:
            data["tags"] = sorted(self.tags)

        if self.attributes:
            data["attributes"] = self.attributes

        assets = self.get_asset_properties()
        if assets:
            data["assets"] = assets

        if include_properties:
            props_dict: Dict[str, Any] = {}
            for k, prop in sorted(self.properties.items()):
                # Exclude internal Name and Source (Source is in script file)
                if k in ("Name", "Source", "UniqueId"):
                    continue
                props_dict[k] = prop.to_json_value()
            data["properties"] = props_dict

        if self.raw_properties:
            data["rawProperties"] = self.raw_properties

        return data

    def __repr__(self) -> str:
        return f"<RobloxInstance class='{self.class_name}' name='{self.name}' referent='{self.referent}' children={len(self.children)}>"
