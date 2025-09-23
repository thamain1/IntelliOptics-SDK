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

from ..models.feedback_in_correct_label import FeedbackInCorrectLabel
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.feedback_in_bboxes_type_0_item import FeedbackInBboxesType0Item


T = TypeVar("T", bound="FeedbackIn")


@_attrs_define
class FeedbackIn:
    """
    Attributes:
        image_query_id (str):
        correct_label (FeedbackInCorrectLabel):
        bboxes (Union[List['FeedbackInBboxesType0Item'], None, Unset]):
    """

    image_query_id: str
    correct_label: FeedbackInCorrectLabel
    bboxes: Union[List["FeedbackInBboxesType0Item"], None, Unset] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        image_query_id = self.image_query_id

        correct_label = self.correct_label.value

        bboxes: Union[List[Dict[str, Any]], None, Unset]
        if isinstance(self.bboxes, Unset):
            bboxes = UNSET
        elif isinstance(self.bboxes, list):
            bboxes = []
            for bboxes_type_0_item_data in self.bboxes:
                bboxes_type_0_item = bboxes_type_0_item_data.to_dict()
                bboxes.append(bboxes_type_0_item)

        else:
            bboxes = self.bboxes

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "image_query_id": image_query_id,
                "correct_label": correct_label,
            }
        )
        if bboxes is not UNSET:
            field_dict["bboxes"] = bboxes

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.feedback_in_bboxes_type_0_item import FeedbackInBboxesType0Item

        d = src_dict.copy()
        image_query_id = d.pop("image_query_id")

        correct_label = FeedbackInCorrectLabel(d.pop("correct_label"))

        def _parse_bboxes(
            data: object,
        ) -> Union[List["FeedbackInBboxesType0Item"], None, Unset]:
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
                    bboxes_type_0_item = FeedbackInBboxesType0Item.from_dict(
                        bboxes_type_0_item_data
                    )

                    bboxes_type_0.append(bboxes_type_0_item)

                return bboxes_type_0
            except:  # noqa: E722
                pass
            return cast(Union[List["FeedbackInBboxesType0Item"], None, Unset], data)

        bboxes = _parse_bboxes(d.pop("bboxes", UNSET))

        feedback_in = cls(
            image_query_id=image_query_id,
            correct_label=correct_label,
            bboxes=bboxes,
        )

        feedback_in.additional_properties = d
        return feedback_in

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
