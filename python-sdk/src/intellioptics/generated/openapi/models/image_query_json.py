from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast, Union
from typing import Union






T = TypeVar("T", bound="ImageQueryJson")



@_attrs_define
class ImageQueryJson:
    """ 
        Attributes:
            detector_id (str):
            image (Union[None, Unset, str]):
            wait (Union[Unset, bool]):  Default: True.
     """

    detector_id: str
    image: Union[None, Unset, str] = UNSET
    wait: Union[Unset, bool] = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        detector_id = self.detector_id

        image: Union[None, Unset, str]
        if isinstance(self.image, Unset):
            image = UNSET
        else:
            image = self.image

        wait = self.wait


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "detector_id": detector_id,
        })
        if image is not UNSET:
            field_dict["image"] = image
        if wait is not UNSET:
            field_dict["wait"] = wait

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        detector_id = d.pop("detector_id")

        def _parse_image(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        image = _parse_image(d.pop("image", UNSET))


        wait = d.pop("wait", UNSET)

        image_query_json = cls(
            detector_id=detector_id,
            image=image,
            wait=wait,
        )


        image_query_json.additional_properties = d
        return image_query_json

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
