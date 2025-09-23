from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.detector_create_mode import DetectorCreateMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="DetectorCreate")


@_attrs_define
class DetectorCreate:
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
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        mode = self.mode.value

        query_text = self.query_text

        threshold = self.threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        mode = DetectorCreateMode(d.pop("mode"))

        query_text = d.pop("query_text")

        threshold = d.pop("threshold", UNSET)

        detector_create = cls(
            name=name,
            mode=mode,
            query_text=query_text,
            threshold=threshold,
        )

        detector_create.additional_properties = d
        return detector_create

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
