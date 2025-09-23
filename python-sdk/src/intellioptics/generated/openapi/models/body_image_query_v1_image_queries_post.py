from collections.abc import Mapping
from io import BytesIO
from typing import (
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, File, FileTypes, Unset

T = TypeVar("T", bound="BodyImageQueryV1ImageQueriesPost")


@_attrs_define
class BodyImageQueryV1ImageQueriesPost:
    """
    Attributes:
        detector_id (str):
        prompt (Union[None, Unset, str]):
        wait (Union[None, Unset, float, str]):
        image (Union[File, None, Unset]):
        confidence_threshold (Union[None, Unset, float, str]):
        metadata (Union[None, Unset, str]):
        inspection_id (Union[None, Unset, str]):
        human_review (Union[None, Unset, str]):
    """

    detector_id: str
    prompt: Union[None, Unset, str] = UNSET
    wait: Union[None, Unset, float, str] = UNSET
    image: Union[File, None, Unset] = UNSET
    confidence_threshold: Union[None, Unset, float, str] = UNSET
    metadata: Union[None, Unset, str] = UNSET
    inspection_id: Union[None, Unset, str] = UNSET
    human_review: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        detector_id = self.detector_id

        prompt: Union[None, Unset, str]
        if isinstance(self.prompt, Unset):
            prompt = UNSET
        else:
            prompt = self.prompt

        wait: Union[None, Unset, float, str]
        if isinstance(self.wait, Unset):
            wait = UNSET
        else:
            wait = self.wait

        image: Union[FileTypes, None, Unset]
        if isinstance(self.image, Unset):
            image = UNSET
        elif isinstance(self.image, File):
            image = self.image.to_tuple()

        else:
            image = self.image

        confidence_threshold: Union[None, Unset, float, str]
        if isinstance(self.confidence_threshold, Unset):
            confidence_threshold = UNSET
        else:
            confidence_threshold = self.confidence_threshold

        metadata: Union[None, Unset, str]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
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
        if prompt is not UNSET:
            field_dict["prompt"] = prompt
        if wait is not UNSET:
            field_dict["wait"] = wait
        if image is not UNSET:
            field_dict["image"] = image
        if confidence_threshold is not UNSET:
            field_dict["confidence_threshold"] = confidence_threshold
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if inspection_id is not UNSET:
            field_dict["inspection_id"] = inspection_id
        if human_review is not UNSET:
            field_dict["human_review"] = human_review

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(
            ("detector_id", (None, str(self.detector_id).encode(), "text/plain"))
        )

        if not isinstance(self.prompt, Unset):
            if isinstance(self.prompt, str):
                files.append(
                    ("prompt", (None, str(self.prompt).encode(), "text/plain"))
                )
            else:
                files.append(
                    ("prompt", (None, str(self.prompt).encode(), "text/plain"))
                )

        if not isinstance(self.wait, Unset):
            if isinstance(self.wait, float):
                files.append(("wait", (None, str(self.wait).encode(), "text/plain")))
            elif isinstance(self.wait, str):
                files.append(("wait", (None, str(self.wait).encode(), "text/plain")))
            else:
                files.append(("wait", (None, str(self.wait).encode(), "text/plain")))

        if not isinstance(self.image, Unset):
            if isinstance(self.image, File):
                files.append(("image", self.image.to_tuple()))
            else:
                files.append(("image", (None, str(self.image).encode(), "text/plain")))

        if not isinstance(self.confidence_threshold, Unset):
            if isinstance(self.confidence_threshold, float):
                files.append(
                    (
                        "confidence_threshold",
                        (None, str(self.confidence_threshold).encode(), "text/plain"),
                    )
                )
            elif isinstance(self.confidence_threshold, str):
                files.append(
                    (
                        "confidence_threshold",
                        (None, str(self.confidence_threshold).encode(), "text/plain"),
                    )
                )
            else:
                files.append(
                    (
                        "confidence_threshold",
                        (None, str(self.confidence_threshold).encode(), "text/plain"),
                    )
                )

        if not isinstance(self.metadata, Unset):
            if isinstance(self.metadata, str):
                files.append(
                    ("metadata", (None, str(self.metadata).encode(), "text/plain"))
                )
            else:
                files.append(
                    ("metadata", (None, str(self.metadata).encode(), "text/plain"))
                )

        if not isinstance(self.inspection_id, Unset):
            if isinstance(self.inspection_id, str):
                files.append(
                    (
                        "inspection_id",
                        (None, str(self.inspection_id).encode(), "text/plain"),
                    )
                )
            else:
                files.append(
                    (
                        "inspection_id",
                        (None, str(self.inspection_id).encode(), "text/plain"),
                    )
                )

        if not isinstance(self.human_review, Unset):
            if isinstance(self.human_review, str):
                files.append(
                    (
                        "human_review",
                        (None, str(self.human_review).encode(), "text/plain"),
                    )
                )
            else:
                files.append(
                    (
                        "human_review",
                        (None, str(self.human_review).encode(), "text/plain"),
                    )
                )

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        detector_id = d.pop("detector_id")

        def _parse_prompt(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        prompt = _parse_prompt(d.pop("prompt", UNSET))

        def _parse_wait(data: object) -> Union[None, Unset, float, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float, str], data)

        wait = _parse_wait(d.pop("wait", UNSET))

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

        def _parse_confidence_threshold(data: object) -> Union[None, Unset, float, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float, str], data)

        confidence_threshold = _parse_confidence_threshold(
            d.pop("confidence_threshold", UNSET)
        )

        def _parse_metadata(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

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

        body_image_query_v1_image_queries_post = cls(
            detector_id=detector_id,
            prompt=prompt,
            wait=wait,
            image=image,
            confidence_threshold=confidence_threshold,
            metadata=metadata,
            inspection_id=inspection_id,
            human_review=human_review,
        )

        body_image_query_v1_image_queries_post.additional_properties = d
        return body_image_query_v1_image_queries_post

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
