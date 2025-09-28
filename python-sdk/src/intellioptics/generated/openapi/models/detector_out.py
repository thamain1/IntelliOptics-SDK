
from typing import Any, Dict, List, Type, TypeVar, Union
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.detector_out_mode import DetectorOutMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="DetectorOut")


@_attrs_define
class DetectorOut:
    """
    Attributes:
        id (str):
        name (str):
        mode (DetectorOutMode):
        query_text (str):
        threshold (float):
        status (Union[Unset, str]):  Default: 'active'.
    """

    id: str
    name: str
    mode: DetectorOutMode
    query_text: str
    threshold: float
    status: Union[Unset, str] = "active"

    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        id = self.id

        name = self.name

        mode = self.mode.value

        query_text = self.query_text

        threshold = self.threshold

        status = self.status

        field_dict: Dict[str, Any] = {}

        field_dict: dict[str, Any] = {}

        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "mode": mode,
                "query_text": query_text,
                "threshold": threshold,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        mode = DetectorOutMode(d.pop("mode"))

        query_text = d.pop("query_text")

        threshold = d.pop("threshold")

        status = d.pop("status", UNSET)

        detector_out = cls(
            id=id,
            name=name,
            mode=mode,
            query_text=query_text,
            threshold=threshold,
            status=status,
        )

        detector_out.additional_properties = d
        return detector_out

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
