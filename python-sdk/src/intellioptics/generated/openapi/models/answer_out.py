
from typing import Any, Dict, List, Type, TypeVar, Union, cast
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.answer_out_answer import AnswerOutAnswer
from ..types import UNSET, Unset

T = TypeVar("T", bound="AnswerOut")


@_attrs_define
class AnswerOut:
    """
    Attributes:
        image_query_id (str):
        answer (AnswerOutAnswer):
        confidence (float):
        latency_ms (Union[None, Unset, int]):
        model_version (Union[None, Unset, str]):  Default: 'demo-v0'.
    """

    image_query_id: str
    answer: AnswerOutAnswer
    confidence: float
    latency_ms: Union[None, Unset, int] = UNSET
    model_version: Union[None, Unset, str] = "demo-v0"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        image_query_id = self.image_query_id

        answer = self.answer.value

        confidence = self.confidence

        latency_ms: Union[None, Unset, int]
        if isinstance(self.latency_ms, Unset):
            latency_ms = UNSET
        else:
            latency_ms = self.latency_ms

        model_version: Union[None, Unset, str]
        if isinstance(self.model_version, Unset):
            model_version = UNSET
        else:
            model_version = self.model_version

        field_dict: Dict[str, Any] = {}
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "image_query_id": image_query_id,
                "answer": answer,
                "confidence": confidence,
            }
        )
        if latency_ms is not UNSET:
            field_dict["latency_ms"] = latency_ms
        if model_version is not UNSET:
            field_dict["model_version"] = model_version

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        image_query_id = d.pop("image_query_id")

        answer = AnswerOutAnswer(d.pop("answer"))

        confidence = d.pop("confidence")

        def _parse_latency_ms(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        latency_ms = _parse_latency_ms(d.pop("latency_ms", UNSET))

        def _parse_model_version(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        model_version = _parse_model_version(d.pop("model_version", UNSET))

        answer_out = cls(
            image_query_id=image_query_id,
            answer=answer,
            confidence=confidence,
            latency_ms=latency_ms,
            model_version=model_version,
        )

        answer_out.additional_properties = d
        return answer_out

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
