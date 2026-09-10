"""
Roblox XML Property Parser.
Parses all Roblox datatypes from XML property tags into typed RobloxProperty models,
with graceful degradation and raw preservation for unknown types.
"""

import base64
import re
import struct
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

from ..model.datatype import (
    Vector2, Vector3, CFrame, Color3, Color3uint8, UDim, UDim2,
    NumberRange, NumberSequence, NumberSequenceKeypoint,
    ColorSequence, ColorSequenceKeypoint, Rect2D, Font,
    PhysicalProperties, ObjectReference
)
from ..model.property import RobloxProperty
from ..utils.logger import ExtractorLogger
from .xml_parser import get_child_text, get_elem_text, elem_to_dict


class PropertyParser:
    def __init__(self, logger: ExtractorLogger, shared_strings: Optional[Dict[str, str]] = None):
        self.logger = logger
        self.shared_strings = shared_strings or {}

    def parse_property(self, elem: ET.Element, instance_path: str = "") -> Optional[RobloxProperty]:
        tag = elem.tag
        prop_name = elem.attrib.get("name", "")
        if not prop_name:
            prop_name = f"Unnamed_{tag}"

        try:
            if tag in ("string", "ProtectedString", "UniqueId"):
                val = elem.text if elem.text is not None else ""
                return RobloxProperty(name=prop_name, type_name=tag, value=val)

            elif tag == "bool":
                txt = (elem.text or "").strip().lower()
                val = txt in ("true", "1")
                return RobloxProperty(name=prop_name, type_name="bool", value=val)

            elif tag in ("int", "int64", "token", "SecurityCapabilities"):
                txt = (elem.text or "").strip()
                val = int(txt) if txt else 0
                return RobloxProperty(name=prop_name, type_name=tag, value=val)

            elif tag in ("float", "double"):
                txt = (elem.text or "").strip()
                if not txt:
                    val = 0.0
                elif txt == "INF":
                    val = float("inf")
                elif txt == "-INF":
                    val = float("-inf")
                elif txt == "NAN":
                    val = float("nan")
                else:
                    val = float(txt)
                return RobloxProperty(name=prop_name, type_name=tag, value=val)

            elif tag == "Vector2":
                x = float(get_child_text(elem, "X", "0"))
                y = float(get_child_text(elem, "Y", "0"))
                return RobloxProperty(name=prop_name, type_name="Vector2", value=Vector2(x, y))

            elif tag == "Vector3":
                x = float(get_child_text(elem, "X", "0"))
                y = float(get_child_text(elem, "Y", "0"))
                z = float(get_child_text(elem, "Z", "0"))
                return RobloxProperty(name=prop_name, type_name="Vector3", value=Vector3(x, y, z))

            elif tag == "CoordinateFrame":
                x = float(get_child_text(elem, "X", "0"))
                y = float(get_child_text(elem, "Y", "0"))
                z = float(get_child_text(elem, "Z", "0"))
                rot = [
                    float(get_child_text(elem, "R00", "1")),
                    float(get_child_text(elem, "R01", "0")),
                    float(get_child_text(elem, "R02", "0")),
                    float(get_child_text(elem, "R10", "0")),
                    float(get_child_text(elem, "R11", "1")),
                    float(get_child_text(elem, "R12", "0")),
                    float(get_child_text(elem, "R20", "0")),
                    float(get_child_text(elem, "R21", "0")),
                    float(get_child_text(elem, "R22", "1")),
                ]
                cframe = CFrame(position=[x, y, z], rotation=rot)
                return RobloxProperty(name=prop_name, type_name="CoordinateFrame", value=cframe)

            elif tag == "OptionalCoordinateFrame":
                cf_elem = elem.find("CFrame")
                if cf_elem is not None:
                    x = float(get_child_text(cf_elem, "X", "0"))
                    y = float(get_child_text(cf_elem, "Y", "0"))
                    z = float(get_child_text(cf_elem, "Z", "0"))
                    rot = [
                        float(get_child_text(cf_elem, "R00", "1")),
                        float(get_child_text(cf_elem, "R01", "0")),
                        float(get_child_text(cf_elem, "R02", "0")),
                        float(get_child_text(cf_elem, "R10", "0")),
                        float(get_child_text(cf_elem, "R11", "1")),
                        float(get_child_text(cf_elem, "R12", "0")),
                        float(get_child_text(cf_elem, "R20", "0")),
                        float(get_child_text(cf_elem, "R21", "0")),
                        float(get_child_text(cf_elem, "R22", "1")),
                    ]
                    cframe = CFrame(position=[x, y, z], rotation=rot)
                    return RobloxProperty(name=prop_name, type_name="OptionalCoordinateFrame", value=cframe)
                return RobloxProperty(name=prop_name, type_name="OptionalCoordinateFrame", value=None)

            elif tag == "Color3":
                r = float(get_child_text(elem, "R", "0"))
                g = float(get_child_text(elem, "G", "0"))
                b = float(get_child_text(elem, "B", "0"))
                return RobloxProperty(name=prop_name, type_name="Color3", value=Color3(r, g, b))

            elif tag == "Color3uint8":
                txt = (elem.text or "").strip()
                val_int = int(txt) if txt else 0
                # Stored as 0xAARRGGBB or 0x00RRGGBB in Roblox uint32
                b = val_int & 0xFF
                g = (val_int >> 8) & 0xFF
                r = (val_int >> 16) & 0xFF
                hex_code = f"#{r:02X}{g:02X}{b:02X}"
                return RobloxProperty(
                    name=prop_name,
                    type_name="Color3uint8",
                    value=Color3uint8(r=r, g=g, b=b, hex=hex_code)
                )

            elif tag == "UDim":
                s = float(get_child_text(elem, "S", "0"))
                o = int(float(get_child_text(elem, "O", "0")))
                return RobloxProperty(name=prop_name, type_name="UDim", value=UDim(s, o))

            elif tag == "UDim2":
                xs = float(get_child_text(elem, "XS", "0"))
                xo = int(float(get_child_text(elem, "XO", "0")))
                ys = float(get_child_text(elem, "YS", "0"))
                yo = int(float(get_child_text(elem, "YO", "0")))
                udim2 = UDim2(x=UDim(xs, xo), y=UDim(ys, yo))
                return RobloxProperty(name=prop_name, type_name="UDim2", value=udim2)

            elif tag == "NumberRange":
                txt = (elem.text or "").strip()
                parts = txt.split()
                if len(parts) >= 2:
                    nr = NumberRange(min=float(parts[0]), max=float(parts[1]))
                elif len(parts) == 1:
                    val = float(parts[0])
                    nr = NumberRange(min=val, max=val)
                else:
                    nr = NumberRange(min=0.0, max=0.0)
                return RobloxProperty(name=prop_name, type_name="NumberRange", value=nr)

            elif tag == "NumberSequence":
                keypoints: List[NumberSequenceKeypoint] = []
                txt = (elem.text or "").strip()
                if txt:
                    # In RBXLX, NumberSequence keypoints can be formatted as whitespace separated numbers:
                    # "time value envelope ..." or XML elements
                    tokens = txt.split()
                    for i in range(0, len(tokens), 3):
                        if i + 2 < len(tokens):
                            keypoints.append(NumberSequenceKeypoint(
                                time=float(tokens[i]),
                                value=float(tokens[i+1]),
                                envelope=float(tokens[i+2])
                            ))
                else:
                    for child in elem.findall("NumberSequenceKeypoint"):
                        t = float(get_child_text(child, "Time", "0"))
                        v = float(get_child_text(child, "Value", "0"))
                        e = float(get_child_text(child, "Envelope", "0"))
                        keypoints.append(NumberSequenceKeypoint(time=t, value=v, envelope=e))
                return RobloxProperty(name=prop_name, type_name="NumberSequence", value=NumberSequence(keypoints))

            elif tag == "ColorSequence":
                c_keypoints: List[ColorSequenceKeypoint] = []
                txt = (elem.text or "").strip()
                if txt:
                    tokens = txt.split()
                    # 5 tokens per keypoint: time r g b envelope
                    for i in range(0, len(tokens), 5):
                        if i + 4 < len(tokens):
                            c_keypoints.append(ColorSequenceKeypoint(
                                time=float(tokens[i]),
                                color=[float(tokens[i+1]), float(tokens[i+2]), float(tokens[i+3])],
                                envelope=float(tokens[i+4])
                            ))
                else:
                    for child in elem.findall("ColorSequenceKeypoint"):
                        t = float(get_child_text(child, "Time", "0"))
                        r = float(get_child_text(child, "R", "0"))
                        g = float(get_child_text(child, "G", "0"))
                        b = float(get_child_text(child, "B", "0"))
                        e = float(get_child_text(child, "Envelope", "0"))
                        c_keypoints.append(ColorSequenceKeypoint(time=t, color=[r, g, b], envelope=e))
                return RobloxProperty(name=prop_name, type_name="ColorSequence", value=ColorSequence(c_keypoints))

            elif tag == "Rect2D":
                min_elem = elem.find("min")
                max_elem = elem.find("max")
                min_pt = [
                    float(get_child_text(min_elem, "X", "0")) if min_elem is not None else 0.0,
                    float(get_child_text(min_elem, "Y", "0")) if min_elem is not None else 0.0,
                ]
                max_pt = [
                    float(get_child_text(max_elem, "X", "0")) if max_elem is not None else 0.0,
                    float(get_child_text(max_elem, "Y", "0")) if max_elem is not None else 0.0,
                ]
                rect = Rect2D(min=min_pt, max=max_pt)
                return RobloxProperty(name=prop_name, type_name="Rect2D", value=rect)

            elif tag == "Font":
                family_elem = elem.find("Family")
                family_url = get_child_text(family_elem, "url", "") if family_elem is not None else ""
                weight = int(get_child_text(elem, "Weight", "400"))
                style = get_child_text(elem, "Style", "Normal")
                cached = get_child_text(elem, "CachedFaceId", "") or None
                font = Font(family=family_url, weight=weight, style=style, cached_face_id=cached)
                return RobloxProperty(name=prop_name, type_name="Font", value=font)

            elif tag == "PhysicalProperties":
                custom = (get_child_text(elem, "CustomPhysics", "false")).lower() in ("true", "1")
                if custom:
                    phys = PhysicalProperties(
                        custom_physics=True,
                        density=float(get_child_text(elem, "Density", "0.7")),
                        friction=float(get_child_text(elem, "Friction", "0.3")),
                        elasticity=float(get_child_text(elem, "Elasticity", "0.5")),
                        friction_weight=float(get_child_text(elem, "FrictionWeight", "1")),
                        elasticity_weight=float(get_child_text(elem, "ElasticityWeight", "1")),
                    )
                else:
                    phys = PhysicalProperties(custom_physics=False)
                return RobloxProperty(name=prop_name, type_name="PhysicalProperties", value=phys)

            elif tag == "Ref":
                ref_val = (elem.text or "").strip()
                status = "null" if not ref_val or ref_val == "null" else "unresolved"
                obj_ref = ObjectReference(referent=ref_val, status=status)
                return RobloxProperty(name=prop_name, type_name="Ref", value=obj_ref)

            elif tag == "Content":
                url_elem = elem.find("url")
                if url_elem is not None and url_elem.text:
                    content_val = url_elem.text.strip()
                elif elem.find("null") is not None:
                    content_val = None
                else:
                    content_val = (elem.text or "").strip() or None
                return RobloxProperty(name=prop_name, type_name="Content", value=content_val)

            elif tag == "BinaryString":
                txt = elem.text or ""
                return RobloxProperty(name=prop_name, type_name="BinaryString", value=txt)

            elif tag == "SharedString":
                key = (elem.text or "").strip()
                resolved_str = self.shared_strings.get(key, key)
                return RobloxProperty(
                    name=prop_name,
                    type_name="SharedString",
                    value=resolved_str,
                    raw=key
                )

            else:
                # Unsupported or custom datatype!
                self.logger.warn(
                    category="UnsupportedDatatype",
                    message=f"Unsupported property tag: <{tag} name='{prop_name}'>",
                    target=instance_path or prop_name,
                )
                raw_dict = elem_to_dict(elem)
                return RobloxProperty(
                    name=prop_name,
                    type_name=tag,
                    value=elem.text or "",
                    raw=raw_dict
                )

        except Exception as ex:
            self.logger.warn(
                category="PropertyParseError",
                message=f"Failed to parse property '{prop_name}' ({tag}): {ex}",
                target=instance_path or prop_name,
            )
            return RobloxProperty(
                name=prop_name,
                type_name=tag,
                value=elem.text or "",
                raw={"error": str(ex), "rawXml": elem_to_dict(elem)}
            )


def decode_tags_binary(tags_text: str) -> List[str]:
    """Decodes CollectionService tags from a BinaryString or text format."""
    if not tags_text:
        return []

    # Check if direct text with delimiters (tabs, newlines, nulls)
    if any(sep in tags_text for sep in ("\t", "\n", "\x00")):
        tags = []
        for part in re.split(r"[\t\n\x00]+", tags_text):
            cleaned = part.strip()
            if cleaned:
                tags.append(cleaned)
        if tags:
            return tags

    # Check if base64 encoded
    try:
        raw_bytes = base64.b64decode(tags_text, validate=True)
    except Exception:
        raw_bytes = tags_text.encode("latin-1", errors="replace")

    # In Roblox BinaryString for Tags, tags are null-separated strings or length-prefixed
    parts = re.split(rb"[\x00\t\n]+", raw_bytes)
    tags: List[str] = []
    for p in parts:
        cleaned = p.strip()
        if cleaned:
            try:
                tag_str = cleaned.decode("utf-8").strip()
                if tag_str and all(32 <= ord(c) < 127 or ord(c) >= 160 for c in tag_str):
                    tags.append(tag_str)
            except UnicodeDecodeError:
                pass

    if not tags and tags_text.strip():
        # Fallback: single tag text
        cleaned = tags_text.strip()
        if cleaned:
            tags.append(cleaned)

    return tags


def decode_attributes_binary(attrs_text: str) -> Dict[str, Any]:
    """
    Decodes serialized Roblox attributes from BinaryString.
    If binary decoding encounters unsupported types, returns raw fallback.
    """
    if not attrs_text:
        return {}

    try:
        raw_bytes = base64.b64decode(attrs_text)
    except Exception:
        raw_bytes = attrs_text.encode("latin-1", errors="replace")

    if len(raw_bytes) < 4:
        return {}

    attributes: Dict[str, Any] = {}
    try:
        offset = 0
        num_attrs = struct.unpack_from("<I", raw_bytes, offset)[0]
        offset += 4

        for _ in range(num_attrs):
            if offset >= len(raw_bytes):
                break
            key_len = struct.unpack_from("<I", raw_bytes, offset)[0]
            offset += 4
            key = raw_bytes[offset:offset + key_len].decode("utf-8", errors="replace")
            offset += key_len

            type_id = raw_bytes[offset]
            offset += 1

            if type_id == 0x02:  # string
                str_len = struct.unpack_from("<I", raw_bytes, offset)[0]
                offset += 4
                val = raw_bytes[offset:offset + str_len].decode("utf-8", errors="replace")
                offset += str_len
                attributes[key] = val
            elif type_id == 0x03:  # bool
                val = bool(raw_bytes[offset])
                offset += 1
                attributes[key] = val
            elif type_id == 0x06:  # float64
                val = struct.unpack_from("<d", raw_bytes, offset)[0]
                offset += 8
                attributes[key] = val
            elif type_id == 0x09:  # UDim
                scale, off = struct.unpack_from("<fi", raw_bytes, offset)
                offset += 8
                attributes[key] = {"scale": scale, "offset": off}
            elif type_id == 0x0A:  # UDim2
                xs, xo, ys, yo = struct.unpack_from("<fifi", raw_bytes, offset)
                offset += 16
                attributes[key] = {"X": {"scale": xs, "offset": xo}, "Y": {"scale": ys, "offset": yo}}
            elif type_id == 0x0E:  # BrickColor
                val = struct.unpack_from("<I", raw_bytes, offset)[0]
                offset += 4
                attributes[key] = val
            elif type_id == 0x0F:  # Color3
                r, g, b = struct.unpack_from("<fff", raw_bytes, offset)
                offset += 12
                attributes[key] = [round(r, 4), round(g, 4), round(b, 4)]
            elif type_id == 0x10:  # Vector2
                x, y = struct.unpack_from("<ff", raw_bytes, offset)
                offset += 8
                attributes[key] = [x, y]
            elif type_id == 0x11:  # Vector3
                x, y, z = struct.unpack_from("<fff", raw_bytes, offset)
                offset += 12
                attributes[key] = [x, y, z]
            else:
                # Unknown attribute type: stop binary parse and keep raw
                attributes[key] = f"<binary_attr_type_{type_id}>"
                break
        return attributes
    except Exception:
        # Fallback if binary structure differs
        return {"_rawAttributesBase64": attrs_text[:100]}
