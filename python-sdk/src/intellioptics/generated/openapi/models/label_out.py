import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.label_out_metadata_type_0 import LabelOutMetadataType0


T = TypeVar("T", bound="LabelOut")


@_attrs_define
class LabelOut:
    """
    Attributes:
        id (str):
        image_query_id (str):
        label (str):
        confidence (Union[None, Unset, float]):
        detector_id (Union[None, Unset, str]):
        user_id (Union[None, Unset, str]):
        metadata (Union['LabelOutMetadataType0', None, Unset]):
        created_at (Union[None, Unset, datetime.datetime]):
    """

    id: str
    image_query_id: str
    label: str
    confidence: Union[None, Unset, float] = UNSET
    detector_id: Union[None, Unset, str] = UNSET
    user_id: Union[None, Unset, str] = UNSET
    metadata: Union["LabelOutMetadataType0", None, Unset] = UNSET
    created_at: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.label_out_metadata_type_0 import LabelOutMetadataType0

        id = self.id

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

        metadata: Union[None, Unset, dict[str, Any]]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, LabelOutMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
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
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.label_out_metadata_type_0 import LabelOutMetadataType0

        d = dict(src_dict)
        id = d.pop("id")

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

        def _parse_metadata(data: object) -> Union["LabelOutMetadataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = LabelOutMetadataType0.from_dict(data)

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(Union["LabelOutMetadataType0", None, Unset], data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_created_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        label_out = cls(
            id=id,
            image_query_id=image_query_id,
            label=label,
            confidence=confidence,
            detector_id=detector_id,
            user_id=user_id,
            metadata=metadata,
            created_at=created_at,
        )

        label_out.additional_properties = d
        return label_out

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
