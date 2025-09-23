from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset
from ..types import UNSET, Unset
from typing import cast, Union
from typing import Union

T = TypeVar("T", bound="LabelSubmission")


@_attrs_define
class LabelSubmission:
    """
        Attributes:
            image_query_id (str):
            label (str):
            confidence (Union[Unset, float]):
            detector_id (Union[Unset, str]):
            user_id (Union[Unset, str]):
            metadata (Union[Unset, dict[str, Any]]):
    """

    image_query_id: str
    label: str
    confidence: Union[Unset, float] = UNSET
    detector_id: Union[Unset, str] = UNSET
    user_id: Union[Unset, str] = UNSET
    metadata: Union[Unset, dict[str, Any]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        image_query_id = self.image_query_id

        label = self.label

        confidence = self.confidence

        detector_id = self.detector_id

        user_id = self.user_id

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "image_query_id": image_query_id,
            "label": label,
        })
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if detector_id is not UNSET:
            field_dict["detector_id"] = detector_id
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        image_query_id = d.pop("image_query_id")

        label = d.pop("label")

        confidence = d.pop("confidence", UNSET)

        detector_id = d.pop("detector_id", UNSET)

        user_id = d.pop("user_id", UNSET)

        metadata = d.pop("metadata", UNSET)

        label_submission = cls(
            image_query_id=image_query_id,
            label=label,
            confidence=confidence,
            detector_id=detector_id,
            user_id=user_id,
            metadata=metadata,
        )

        label_submission.additional_properties = d
        return label_submission

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
