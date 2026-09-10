"""
Tests for Object Reference resolution and broken reference handling.
"""

from src.parser.rbxlx_parser import RbxlxParser
from src.resolver.reference_resolver import ReferenceResolver
from src.utils.logger import ExtractorLogger


def test_object_references_resolution(get_fixture_path):
    logger = ExtractorLogger()
    parser = RbxlxParser(logger=logger)
    file_path = get_fixture_path("object_references.rbxlx")

    data_model, ref_map = parser.parse_file(file_path)

    resolver = ReferenceResolver(logger=logger, instances_by_referent=ref_map)
    resolver.resolve_all(data_model)

    # 1. Car PrimaryPart -> Body
    car = ref_map["RBX_CAR"]
    primary_part_ref = car.properties["PrimaryPart"].value
    assert primary_part_ref.status == "resolved"
    assert primary_part_ref.referent == "RBX_BODY"
    assert primary_part_ref.target_path == "Workspace.Car.Body"
    assert primary_part_ref.target_name == "Body"
    assert primary_part_ref.target_class == "Part"

    # 2. TargetValue -> Body
    target_val = ref_map["RBX_TARGET_VAL"]
    val_ref = target_val.properties["Value"].value
    assert val_ref.status == "resolved"
    assert val_ref.target_path == "Workspace.Car.Body"

    # 3. Broken Target -> RBX_NONEXISTENT_GHOST
    broken_val = ref_map["RBX_BROKEN_VAL"]
    broken_ref = broken_val.properties["Value"].value
    assert broken_ref.status == "broken"
    assert broken_ref.target_path is None

    # 4. Null Ref Part -> null
    null_part = ref_map["RBX_NULL_REF"]
    null_ref = null_part.properties["PrimaryPart"].value
    assert null_ref.status == "null"

    # Verify counts
    assert resolver.total_references == 4
    assert resolver.resolved_references == 2
    assert resolver.broken_references == 1

    # Verify warning was recorded
    assert any("missing referent 'RBX_NONEXISTENT_GHOST'" in w.message for w in logger.warnings)
