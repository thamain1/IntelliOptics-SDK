
from io import BytesIO
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, File, FileJsonType, Unset
from .. import types
from ..types import UNSET, File, FileTypes, Unset

T = TypeVar("T", bound="BodyImageQueryV1ImageQueriesPost")


@_attrs_define
class BodyImageQueryV1ImageQueriesPost:
    """
    Attributes:
        detector_id (str):
        wait (Union[Unset, bool]):  Default: True.
        image (Union[File, None, Unset]):
    """

    detector_id: str
    wait: Union[Unset, bool] = True
    image: Union[File, None, Unset] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        detector_id = self.detector_id

        wait = self.wait

        image: Union[FileJsonType, None, Unset]
        if isinstance(self.image, Unset):
            image = UNSET
        elif isinstance(self.image, File):
            image = self.image.to_tuple()

        else:
            image = self.image


        field_dict: Dict[str, Any] = {}

        field_dict: dict[str, Any] = {}

        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "detector_id": detector_id,
            }
        )
        if wait is not UNSET:
            field_dict["wait"] = wait
        if image is not UNSET:
            field_dict["image"] = image

        return field_dict


    def to_multipart(self) -> Dict[str, Any]:
        detector_id = (None, str(self.detector_id).encode(), "text/plain")

        wait = (
            self.wait
            if isinstance(self.wait, Unset)
            else (None, str(self.wait).encode(), "text/plain")
        )

        image: Union[Tuple[None, bytes, str], Unset]

        if isinstance(self.image, Unset):
            image = UNSET
        elif isinstance(self.image, File):
            image = self.image.to_tuple()
        else:
            image = (None, str(self.image).encode(), "text/plain")

        field_dict: Dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = (None, str(prop).encode(), "text/plain")

        field_dict.update(
            {
                "detector_id": detector_id,
            }
        )
        if wait is not UNSET:
            field_dict["wait"] = wait
        if image is not UNSET:
            field_dict["image"] = image

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("detector_id", (None, str(self.detector_id).encode(), "text/plain")))

        if not isinstance(self.wait, Unset):
            files.append(("wait", (None, str(self.wait).encode(), "text/plain")))

        if not isinstance(self.image, Unset):
            if isinstance(self.image, File):
                files.append(("image", self.image.to_tuple()))
            else:
                files.append(("image", (None, str(self.image).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        detector_id = d.pop("detector_id")

        wait = d.pop("wait", UNSET)

        def _parse_image(data: object) -> Union[File, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, bytes):
                    raise TypeError()
                image_type_0 = File(payload=BytesIO(data))

                return image_type_0
            except:  # noqa: E722
                pass
            return cast(Union[File, None, Unset], data)

        image = _parse_image(d.pop("image", UNSET))

        body_image_query_v1_image_queries_post = cls(
            detector_id=detector_id,
            wait=wait,
            image=image,
        )

        body_image_query_v1_image_queries_post.additional_properties = d
        return body_image_query_v1_image_queries_post

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
