"""
Tests for Roblox datatypes parsed from complex_datatypes.rbxlx.
"""

from src.parser.rbxlx_parser import RbxlxParser
from src.utils.logger import ExtractorLogger
from src.model.datatype import (
    Vector2, Vector3, CFrame, Color3, Color3uint8, UDim, UDim2,
    NumberRange, NumberSequence, ColorSequence, Rect2D, Font, PhysicalProperties
)


def test_complex_datatypes(get_fixture_path):
    logger = ExtractorLogger()
    parser = RbxlxParser(logger=logger)
    file_path = get_fixture_path("complex_datatypes.rbxlx")

    data_model, ref_map = parser.parse_file(file_path)
    part = ref_map["RBX_COMPLEX_PART"]
    props = part.properties

    # Vector2
    v2 = props["CustomVector2"].value
    assert isinstance(v2, Vector2)
    assert v2.x == 10.5 and v2.y == 20.5
    assert v2.to_json() == [10.5, 20.5]

    # Vector3
    v3 = props["Size"].value
    assert isinstance(v3, Vector3)
    assert v3.x == 4.0 and v3.y == 1.0 and v3.z == 4.0
    assert v3.to_json() == [4.0, 1.0, 4.0]

    # CFrame
    cf = props["CFrame"].value
    assert isinstance(cf, CFrame)
    assert cf.position == [0.0, 5.0, 0.0]
    assert cf.rotation == [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

    # Color3
    c3 = props["Color"].value
    assert isinstance(c3, Color3)
    assert c3.r == 1.0 and c3.g == 0.5 and c3.b == 0.0

    # Color3uint8
    c_u8 = props["Color3uint8"].value
    assert isinstance(c_u8, Color3uint8)
    assert c_u8.hex.startswith("#")

    # UDim & UDim2
    udim = props["CustomUDim"].value
    assert isinstance(udim, UDim)
    assert udim.scale == 0.5 and udim.offset == 100

    udim2 = props["CustomUDim2"].value
    assert isinstance(udim2, UDim2)
    assert udim2.x.scale == 0.5 and udim2.x.offset == 10
    assert udim2.y.scale == 0.25 and udim2.y.offset == 20

    # NumberRange
    nr = props["CustomRange"].value
    assert isinstance(nr, NumberRange)
    assert nr.min == 5.0 and nr.max == 50.0

    # NumberSequence
    nseq = props["CustomNumberSeq"].value
    assert isinstance(nseq, NumberSequence)
    assert len(nseq.keypoints) == 3
    assert nseq.keypoints[0].time == 0.0
    assert nseq.keypoints[0].value == 1.0

    # ColorSequence
    cseq = props["CustomColorSeq"].value
    assert isinstance(cseq, ColorSequence)
    assert len(cseq.keypoints) == 2

    # Rect2D
    rect = props["CustomRect"].value
    assert isinstance(rect, Rect2D)
    assert rect.min == [10.0, 20.0]
    assert rect.max == [100.0, 200.0]

    # Font
    font = props["CustomFont"].value
    assert isinstance(font, Font)
    assert "BuilderSans.json" in font.family
    assert font.weight == 700

    # PhysicalProperties
    phys = props["CustomPhysics"].value
    assert isinstance(phys, PhysicalProperties)
    assert phys.custom_physics is True
    assert phys.density == 0.8

    # Content
    content = props["TextureID"].value
    assert content == "rbxassetid://1337420"

    # Tags
    assert "PlayerSpawn" in part.tags
    assert "SafeZone" in part.tags
