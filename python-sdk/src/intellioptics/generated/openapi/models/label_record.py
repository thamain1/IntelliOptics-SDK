"""Response payload returned after creating a label."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional, TypeVar

from attrs import define as _attrs_define

from .label_create import LabelCreate

T = TypeVar("T", bound="LabelRecord")


@_attrs_define
class LabelRecord(LabelCreate):
    """Extends :class:`LabelCreate` with server-generated fields."""

    id: Optional[str] = None
    created_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        field_dict = super().to_dict()
        if self.id is not None:
            field_dict["id"] = self.id
        if self.created_at is not None:
            field_dict["created_at"] = self.created_at
        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d: Dict[str, Any] = dict(src_dict)
        id_ = d.pop("id", None)
        created_at = d.pop("created_at", None)
        base = LabelCreate.from_dict(d)
        label_record = cls(
            image_query_id=base.image_query_id,
            label=base.label,
            confidence=base.confidence,
            detector_id=base.detector_id,
            user_id=base.user_id,
            metadata=base.metadata,
            id=id_,
            created_at=created_at,
        )
        label_record.additional_properties = base.additional_properties
        return label_record
