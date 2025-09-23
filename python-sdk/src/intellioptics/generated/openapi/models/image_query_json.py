from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.image_query_json_metadata_type_0 import ImageQueryJsonMetadataType0


T = TypeVar("T", bound="ImageQueryJson")


@_attrs_define
class ImageQueryJson:
    """
    Attributes:
        detector_id (str):
        image (Union[None, Unset, str]):
        image_url (Union[None, Unset, str]):
        prompt (Union[None, Unset, str]):
        wait (Union[None, Unset, float]):
        confidence_threshold (Union[None, Unset, float]):
        metadata (Union['ImageQueryJsonMetadataType0', None, Unset]):
        inspection_id (Union[None, Unset, str]):
        human_review (Union[None, Unset, str]):
    """

    detector_id: str
    image: Union[None, Unset, str] = UNSET
    image_url: Union[None, Unset, str] = UNSET
    prompt: Union[None, Unset, str] = UNSET
    wait: Union[None, Unset, float] = UNSET
    confidence_threshold: Union[None, Unset, float] = UNSET
    metadata: Union["ImageQueryJsonMetadataType0", None, Unset] = UNSET
    inspection_id: Union[None, Unset, str] = UNSET
    human_review: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.image_query_json_metadata_type_0 import (
            ImageQueryJsonMetadataType0,
        )

        detector_id = self.detector_id

        image: Union[None, Unset, str]
        if isinstance(self.image, Unset):
            image = UNSET
        else:
            image = self.image

        image_url: Union[None, Unset, str]
        if isinstance(self.image_url, Unset):
            image_url = UNSET
        else:
            image_url = self.image_url

        prompt: Union[None, Unset, str]
        if isinstance(self.prompt, Unset):
            prompt = UNSET
        else:
            prompt = self.prompt

        wait: Union[None, Unset, float]
        if isinstance(self.wait, Unset):
            wait = UNSET
        else:
            wait = self.wait

        confidence_threshold: Union[None, Unset, float]
        if isinstance(self.confidence_threshold, Unset):
            confidence_threshold = UNSET
        else:
            confidence_threshold = self.confidence_threshold

        metadata: Union[None, Unset, dict[str, Any]]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ImageQueryJsonMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        inspection_id: Union[None, Unset, str]
        if isinstance(self.inspection_id, Unset):
            inspection_id = UNSET
        else:
            inspection_id = self.inspection_id

        human_review: Union[None, Unset, str]
        if isinstance(self.human_review, Unset):
            human_review = UNSET
        else:
            human_review = self.human_review

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "detector_id": detector_id,
            }
        )
        if image is not UNSET:
            field_dict["image"] = image
        if image_url is not UNSET:
            field_dict["image_url"] = image_url
        if prompt is not UNSET:
            field_dict["prompt"] = prompt
        if wait is not UNSET:
            field_dict["wait"] = wait
        if confidence_threshold is not UNSET:
            field_dict["confidence_threshold"] = confidence_threshold
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if inspection_id is not UNSET:
            field_dict["inspection_id"] = inspection_id
        if human_review is not UNSET:
            field_dict["human_review"] = human_review

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.image_query_json_metadata_type_0 import (
            ImageQueryJsonMetadataType0,
        )

        d = dict(src_dict)
        detector_id = d.pop("detector_id")

        def _parse_image(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        image = _parse_image(d.pop("image", UNSET))

        def _parse_image_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        image_url = _parse_image_url(d.pop("image_url", UNSET))

        def _parse_prompt(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        prompt = _parse_prompt(d.pop("prompt", UNSET))

        def _parse_wait(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        wait = _parse_wait(d.pop("wait", UNSET))

        def _parse_confidence_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        confidence_threshold = _parse_confidence_threshold(
            d.pop("confidence_threshold", UNSET)
        )

        def _parse_metadata(
            data: object,
        ) -> Union["ImageQueryJsonMetadataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ImageQueryJsonMetadataType0.from_dict(data)

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ImageQueryJsonMetadataType0", None, Unset], data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_inspection_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        inspection_id = _parse_inspection_id(d.pop("inspection_id", UNSET))

        def _parse_human_review(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        human_review = _parse_human_review(d.pop("human_review", UNSET))

        image_query_json = cls(
            detector_id=detector_id,
            image=image,
            image_url=image_url,
            prompt=prompt,
            wait=wait,
            confidence_threshold=confidence_threshold,
            metadata=metadata,
            inspection_id=inspection_id,
            human_review=human_review,
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
