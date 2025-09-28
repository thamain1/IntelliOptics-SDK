"""Envelope for detector listings."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, List, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .detector_out import DetectorOut

T = TypeVar("T", bound="DetectorList")


@_attrs_define
class DetectorList:
    """Response wrapper for ``GET /v1/detectors``."""

    items: List[DetectorOut]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict["items"] = [item.to_dict() for item in self.items]
        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        items = [DetectorOut.from_dict(item) for item in d.pop("items", [])]
        detector_list = cls(items=items)
        detector_list.additional_properties = d
        return detector_list

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
