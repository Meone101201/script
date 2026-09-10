"""
Roblox datatype representations and serialization helpers.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class Vector2:
    x: float
    y: float

    def to_json(self) -> List[float]:
        return [self.x, self.y]


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def to_json(self) -> List[float]:
        return [self.x, self.y, self.z]


@dataclass
class CFrame:
    position: List[float]  # [X, Y, Z]
    rotation: List[float]  # [R00, R01, R02, R10, R11, R12, R20, R21, R22]

    def to_json(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "rotation": self.rotation,
        }


@dataclass
class Color3:
    r: float
    g: float
    b: float

    def to_json(self) -> List[float]:
        return [round(self.r, 5), round(self.g, 5), round(self.b, 5)]


@dataclass
class Color3uint8:
    r: int
    g: int
    b: int
    hex: str

    def to_json(self) -> Dict[str, Any]:
        return {
            "rgb": [self.r, self.g, self.b],
            "hex": self.hex,
        }


@dataclass
class UDim:
    scale: float
    offset: int

    def to_json(self) -> Dict[str, Any]:
        return {"scale": self.scale, "offset": self.offset}


@dataclass
class UDim2:
    x: UDim
    y: UDim

    def to_json(self) -> Dict[str, Any]:
        return {
            "X": self.x.to_json(),
            "Y": self.y.to_json(),
        }


@dataclass
class NumberRange:
    min: float
    max: float

    def to_json(self) -> List[float]:
        return [self.min, self.max]


@dataclass
class NumberSequenceKeypoint:
    time: float
    value: float
    envelope: float = 0.0

    def to_json(self) -> Dict[str, float]:
        return {
            "time": self.time,
            "value": self.value,
            "envelope": self.envelope,
        }


@dataclass
class NumberSequence:
    keypoints: List[NumberSequenceKeypoint]

    def to_json(self) -> List[Dict[str, float]]:
        return [kp.to_json() for kp in self.keypoints]


@dataclass
class ColorSequenceKeypoint:
    time: float
    color: List[float]  # [R, G, B]
    envelope: float = 0.0

    def to_json(self) -> Dict[str, Any]:
        return {
            "time": self.time,
            "color": self.color,
            "envelope": self.envelope,
        }


@dataclass
class ColorSequence:
    keypoints: List[ColorSequenceKeypoint]

    def to_json(self) -> List[Dict[str, Any]]:
        return [kp.to_json() for kp in self.keypoints]


@dataclass
class Rect2D:
    min: List[float]  # [X, Y]
    max: List[float]  # [X, Y]

    def to_json(self) -> Dict[str, List[float]]:
        return {
            "min": self.min,
            "max": self.max,
        }


@dataclass
class Font:
    family: str
    weight: int = 400
    style: str = "Normal"
    cached_face_id: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        data = {
            "family": self.family,
            "weight": self.weight,
            "style": self.style,
        }
        if self.cached_face_id:
            data["cachedFaceId"] = self.cached_face_id
        return data


@dataclass
class PhysicalProperties:
    custom_physics: bool
    density: Optional[float] = None
    friction: Optional[float] = None
    elasticity: Optional[float] = None
    friction_weight: Optional[float] = None
    elasticity_weight: Optional[float] = None

    def to_json(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"customPhysics": self.custom_physics}
        if self.custom_physics:
            data.update({
                "density": self.density,
                "friction": self.friction,
                "elasticity": self.elasticity,
                "frictionWeight": self.friction_weight,
                "elasticityWeight": self.elasticity_weight,
            })
        return data


@dataclass
class ObjectReference:
    referent: str
    target_path: Optional[str] = None
    target_name: Optional[str] = None
    target_class: Optional[str] = None
    status: str = "unresolved"  # unresolved, resolved, broken, null

    def to_json(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {"referent": self.referent}
        if self.target_path:
            res["targetPath"] = self.target_path
        if self.target_name:
            res["targetName"] = self.target_name
        if self.target_class:
            res["targetClass"] = self.target_class
        if self.status != "resolved":
            res["status"] = self.status
        return res
