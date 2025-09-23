"""Request payload for label submission."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="LabelCreate")


@_attrs_define
class LabelCreate:
    """Body accepted by ``POST /v1/labels``."""

    image_query_id: str
    label: str
    confidence: Optional[float] = None
    detector_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "image_query_id": self.image_query_id,
            "label": self.label,
        })
        if self.confidence is not None:
            field_dict["confidence"] = self.confidence
        if self.detector_id is not None:
            field_dict["detector_id"] = self.detector_id
        if self.user_id is not None:
            field_dict["user_id"] = self.user_id
        if self.metadata is not None:
            field_dict["metadata"] = self.metadata
        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        label_create = cls(
            image_query_id=d.pop("image_query_id"),
            label=d.pop("label"),
            confidence=d.pop("confidence", None),
            detector_id=d.pop("detector_id", None),
            user_id=d.pop("user_id", None),
            metadata=d.pop("metadata", None),
        )
        label_create.additional_properties = d
        return label_create

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
