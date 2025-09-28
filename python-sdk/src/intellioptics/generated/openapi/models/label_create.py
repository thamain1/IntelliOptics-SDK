"""Request payload for label submission."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional, TypeVar
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.label_create_metadata_type_0 import LabelCreateMetadataType0


T = TypeVar("T", bound="LabelCreate")


@_attrs_define
class LabelCreate:

    """Body accepted by ``POST /v1/labels``."""

    image_query_id: str
    label: str
    confidence: Optional[float] = None
    detector_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "image_query_id": self.image_query_id,
            "label": self.label,
        })
        if self.confidence is not None:
            field_dict["confidence"] = self.confidence
        if self.detector_id is not None:
            field_dict["detector_id"] = self.detector_id
        if self.user_id is not None:
            field_dict["user_id"] = self.user_id
        if self.metadata is not None:
            field_dict["metadata"] = self.metadata
        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        label_create = cls(
            image_query_id=d.pop("image_query_id"),
            label=d.pop("label"),
            confidence=d.pop("confidence", None),
            detector_id=d.pop("detector_id", None),
            user_id=d.pop("user_id", None),
            metadata=d.pop("metadata", None),
        )
    """
    Attributes:
        image_query_id (str):
        label (str):
        confidence (Union[None, Unset, float]):
        detector_id (Union[None, Unset, str]):
        user_id (Union[None, Unset, str]):
        metadata (Union['LabelCreateMetadataType0', None, Unset]):
    """

    image_query_id: str
    label: str
    confidence: Union[None, Unset, float] = UNSET
    detector_id: Union[None, Unset, str] = UNSET
    user_id: Union[None, Unset, str] = UNSET
    metadata: Union["LabelCreateMetadataType0", None, Unset] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.label_create_metadata_type_0 import LabelCreateMetadataType0

        image_query_id = self.image_query_id

        label = self.label

        confidence: Union[None, Unset, float]
        if isinstance(self.confidence, Unset):
            confidence = UNSET
        else:
            confidence = self.confidence

        detector_id: Union[None, Unset, str]
        if isinstance(self.detector_id, Unset):
            detector_id = UNSET
        else:
            detector_id = self.detector_id

        user_id: Union[None, Unset, str]
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        metadata: Union[Dict[str, Any], None, Unset]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, LabelCreateMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "image_query_id": image_query_id,
                "label": label,
            }
        )
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.label_create_metadata_type_0 import LabelCreateMetadataType0

        d = src_dict.copy()
        image_query_id = d.pop("image_query_id")

        label = d.pop("label")

        def _parse_confidence(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        confidence = _parse_confidence(d.pop("confidence", UNSET))

        def _parse_detector_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        detector_id = _parse_detector_id(d.pop("detector_id", UNSET))

        def _parse_user_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_metadata(
            data: object,
        ) -> Union["LabelCreateMetadataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = LabelCreateMetadataType0.from_dict(data)

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(Union["LabelCreateMetadataType0", None, Unset], data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        label_create = cls(
            image_query_id=image_query_id,
            label=label,
            confidence=confidence,
            detector_id=detector_id,
            user_id=user_id,
            metadata=metadata,
        )

        label_create.additional_properties = d
        return label_create

    @property

    def additional_keys(self) -> list[str]:

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
