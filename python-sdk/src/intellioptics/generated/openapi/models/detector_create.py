
"""Data model for creating detectors."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from typing import Any, Dict, List, Type, TypeVar, Union
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.detector_create_mode import DetectorCreateMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="DetectorCreate")


@_attrs_define
class DetectorCreate:
    """Payload accepted by ``POST /v1/detectors``.

    Attributes:
        name: Human friendly detector name.
        labels: Optional label hints for the detector.
    """

    name: str
    labels: list[str] = _attrs_field(factory=list)
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
    """
    Attributes:
        name (str):
        mode (DetectorCreateMode):
        query_text (str):
        threshold (Union[Unset, float]):  Default: 0.75.
    """

    name: str
    mode: DetectorCreateMode
    query_text: str
    threshold: Union[Unset, float] = 0.75
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        name = self.name

        mode = self.mode.value

        query_text = self.query_text

        threshold = self.threshold


        field_dict: Dict[str, Any] = {}

        field_dict: dict[str, Any] = {}

        field_dict.update(self.additional_properties)

        field_dict.update({
            "name": self.name,
            "labels": list(self.labels),
        })

        field_dict.update(
            {
                "name": name,
                "mode": mode,
                "query_text": query_text,
            }
        )
        if threshold is not UNSET:
            field_dict["threshold"] = threshold

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        labels = list(d.pop("labels", []))


        mode = DetectorCreateMode(d.pop("mode"))

        query_text = d.pop("query_text")

        threshold = d.pop("threshold", UNSET)

        detector_create = cls(
            name=name,
            labels=labels,
        )

        detector_create.additional_properties = d
        return detector_create

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
