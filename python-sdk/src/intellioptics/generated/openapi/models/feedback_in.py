from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.feedback_in_bboxes_type_0_item import FeedbackInBboxesType0Item


T = TypeVar("T", bound="FeedbackIn")


@_attrs_define
class FeedbackIn:
    """
    Attributes:
        iq_id (str):
        correct_label (str):
        bboxes (Union[None, Unset, list['FeedbackInBboxesType0Item']]):
        notes (Union[None, Unset, str]):
    """

    iq_id: str
    correct_label: str
    bboxes: Union[None, Unset, list["FeedbackInBboxesType0Item"]] = UNSET
    notes: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        iq_id = self.iq_id

        correct_label = self.correct_label

        bboxes: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.bboxes, Unset):
            bboxes = UNSET
        elif isinstance(self.bboxes, list):
            bboxes = []
            for bboxes_type_0_item_data in self.bboxes:
                bboxes_type_0_item = bboxes_type_0_item_data.to_dict()
                bboxes.append(bboxes_type_0_item)

        else:
            bboxes = self.bboxes

        notes: Union[None, Unset, str]
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "iq_id": iq_id,
                "correct_label": correct_label,
            }
        )
        if bboxes is not UNSET:
            field_dict["bboxes"] = bboxes
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.feedback_in_bboxes_type_0_item import FeedbackInBboxesType0Item

        d = dict(src_dict)
        iq_id = d.pop("iq_id")

        correct_label = d.pop("correct_label")

        def _parse_bboxes(data: object) -> Union[None, Unset, list["FeedbackInBboxesType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                bboxes_type_0 = []
                _bboxes_type_0 = data
                for bboxes_type_0_item_data in _bboxes_type_0:
                    bboxes_type_0_item = FeedbackInBboxesType0Item.from_dict(bboxes_type_0_item_data)

                    bboxes_type_0.append(bboxes_type_0_item)

                return bboxes_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["FeedbackInBboxesType0Item"]], data)

        bboxes = _parse_bboxes(d.pop("bboxes", UNSET))

        def _parse_notes(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        notes = _parse_notes(d.pop("notes", UNSET))

        feedback_in = cls(
            iq_id=iq_id,
            correct_label=correct_label,
            bboxes=bboxes,
            notes=notes,
        )

        feedback_in.additional_properties = d
        return feedback_in

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
