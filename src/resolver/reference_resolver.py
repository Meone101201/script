"""
Roblox Object Reference Resolver.
Resolves Ref property referents into exact canonical instance paths and targets,
and logs warnings for broken/dangling references.
"""

from typing import Dict, List, Optional
from ..model.instance import RobloxInstance
from ..model.datatype import ObjectReference
from ..utils.logger import ExtractorLogger


class ReferenceResolver:
    def __init__(self, logger: ExtractorLogger, instances_by_referent: Dict[str, RobloxInstance]):
        self.logger = logger
        self.instances_by_referent = instances_by_referent
        self.total_references = 0
        self.resolved_references = 0
        self.broken_references = 0

    def resolve_all(self, root: RobloxInstance) -> None:
        """Traverses the instance tree and resolves all Ref properties."""
        self.total_references = 0
        self.resolved_references = 0
        self.broken_references = 0

        self._resolve_instance(root)

        self.logger.stats["totalReferences"] = self.total_references
        self.logger.info(
            f"Resolved {self.resolved_references}/{self.total_references} object references "
            f"({self.broken_references} broken)",
            prefix="RESOLVER"
        )

    def _resolve_instance(self, instance: RobloxInstance) -> None:
        for prop_name, prop in instance.properties.items():
            if prop.type_name == "Ref" and isinstance(prop.value, ObjectReference):
                ref_obj: ObjectReference = prop.value
                self.total_references += 1

                if not ref_obj.referent or ref_obj.referent == "null":
                    ref_obj.status = "null"
                    continue

                if ref_obj.referent in self.instances_by_referent:
                    target = self.instances_by_referent[ref_obj.referent]
                    ref_obj.status = "resolved"
                    ref_obj.target_path = target.get_full_path()
                    ref_obj.target_name = target.name
                    ref_obj.target_class = target.class_name
                    self.resolved_references += 1
                else:
                    ref_obj.status = "broken"
                    self.broken_references += 1
                    self.logger.warn(
                        category="BrokenReference",
                        message=f"Property '{prop_name}' references missing referent '{ref_obj.referent}'",
                        target=instance.get_full_path(),
                    )

        for child in instance.children:
            self._resolve_instance(child)
