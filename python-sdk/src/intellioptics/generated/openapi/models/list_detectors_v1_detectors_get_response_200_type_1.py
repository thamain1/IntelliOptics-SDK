from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
  from ..models.detector_out import DetectorOut





T = TypeVar("T", bound="ListDetectorsV1DetectorsGetResponse200Type1")



@_attrs_define
class ListDetectorsV1DetectorsGetResponse200Type1:
    """ 
        Attributes:
            items (list['DetectorOut']):
     """

    items: list['DetectorOut']
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.detector_out import DetectorOut
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)




        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "items": items,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.detector_out import DetectorOut
        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in (_items):
            items_item = DetectorOut.from_dict(items_item_data)



            items.append(items_item)


        list_detectors_v1_detectors_get_response_200_type_1 = cls(
            items=items,
        )


        list_detectors_v1_detectors_get_response_200_type_1.additional_properties = d
        return list_detectors_v1_detectors_get_response_200_type_1

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
