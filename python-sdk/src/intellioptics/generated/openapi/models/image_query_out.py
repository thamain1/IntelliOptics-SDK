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
    from ..models.image_query_out_extra_type_0 import ImageQueryOutExtraType0
    from ..models.image_query_out_result_type_0 import ImageQueryOutResultType0


T = TypeVar("T", bound="ImageQueryOut")


@_attrs_define
class ImageQueryOut:
    """
    Attributes:
        id (str):
        status (str):
        detector_id (Union[None, Unset, str]):
        result_type (Union[None, Unset, str]):
        result (Union['ImageQueryOutResultType0', None, Unset]):
        confidence (Union[None, Unset, float]):
        label (Union[None, Unset, str]):
        extra (Union['ImageQueryOutExtraType0', None, Unset]):
    """

    id: str
    status: str
    detector_id: Union[None, Unset, str] = UNSET
    result_type: Union[None, Unset, str] = UNSET
    result: Union["ImageQueryOutResultType0", None, Unset] = UNSET
    confidence: Union[None, Unset, float] = UNSET
    label: Union[None, Unset, str] = UNSET
    extra: Union["ImageQueryOutExtraType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.image_query_out_extra_type_0 import ImageQueryOutExtraType0
        from ..models.image_query_out_result_type_0 import ImageQueryOutResultType0

        id = self.id

        status = self.status

        detector_id: Union[None, Unset, str]
        if isinstance(self.detector_id, Unset):
            detector_id = UNSET
        else:
            detector_id = self.detector_id

        result_type: Union[None, Unset, str]
        if isinstance(self.result_type, Unset):
            result_type = UNSET
        else:
            result_type = self.result_type

        result: Union[None, Unset, dict[str, Any]]
        if isinstance(self.result, Unset):
            result = UNSET
        elif isinstance(self.result, ImageQueryOutResultType0):
            result = self.result.to_dict()
        else:
            result = self.result

        confidence: Union[None, Unset, float]
        if isinstance(self.confidence, Unset):
            confidence = UNSET
        else:
            confidence = self.confidence

        label: Union[None, Unset, str]
        if isinstance(self.label, Unset):
            label = UNSET
        else:
            label = self.label

        extra: Union[None, Unset, dict[str, Any]]
        if isinstance(self.extra, Unset):
            extra = UNSET
        elif isinstance(self.extra, ImageQueryOutExtraType0):
            extra = self.extra.to_dict()
        else:
            extra = self.extra

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "status": status,
            }
        )
        if detector_id is not UNSET:
            field_dict["detector_id"] = detector_id
        if result_type is not UNSET:
            field_dict["result_type"] = result_type
        if result is not UNSET:
            field_dict["result"] = result
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if label is not UNSET:
            field_dict["label"] = label
        if extra is not UNSET:
            field_dict["extra"] = extra

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.image_query_out_extra_type_0 import ImageQueryOutExtraType0
        from ..models.image_query_out_result_type_0 import ImageQueryOutResultType0

        d = dict(src_dict)
        id = d.pop("id")

        status = d.pop("status")

        def _parse_detector_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        detector_id = _parse_detector_id(d.pop("detector_id", UNSET))

        def _parse_result_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        result_type = _parse_result_type(d.pop("result_type", UNSET))

        def _parse_result(
            data: object,
        ) -> Union["ImageQueryOutResultType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                result_type_0 = ImageQueryOutResultType0.from_dict(data)

                return result_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ImageQueryOutResultType0", None, Unset], data)

        result = _parse_result(d.pop("result", UNSET))

        def _parse_confidence(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        confidence = _parse_confidence(d.pop("confidence", UNSET))

        def _parse_label(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        label = _parse_label(d.pop("label", UNSET))

        def _parse_extra(data: object) -> Union["ImageQueryOutExtraType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                extra_type_0 = ImageQueryOutExtraType0.from_dict(data)

                return extra_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ImageQueryOutExtraType0", None, Unset], data)

        extra = _parse_extra(d.pop("extra", UNSET))

        image_query_out = cls(
            id=id,
            status=status,
            detector_id=detector_id,
            result_type=result_type,
            result=result,
            confidence=confidence,
            label=label,
            extra=extra,
        )

        image_query_out.additional_properties = d
        return image_query_out

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
