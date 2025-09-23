from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
from typing import Union
import datetime

if TYPE_CHECKING:
  from ..models.detector_out_metadata import DetectorOutMetadata





T = TypeVar("T", bound="DetectorOut")



@_attrs_define
class DetectorOut:
    """ 
        Attributes:
            id (str):
            name (str):
            labels (Union[Unset, list[str]]):
            status (Union[Unset, str]):  Default: 'active'.
            created_at (Union[Unset, datetime.datetime]):
            updated_at (Union[Unset, datetime.datetime]):
            metadata (Union[Unset, DetectorOutMetadata]):
     """

    id: str
    name: str
    labels: Union[Unset, list[str]] = UNSET
    status: Union[Unset, str] = 'active'
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    metadata: Union[Unset, 'DetectorOutMetadata'] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.detector_out_metadata import DetectorOutMetadata
        id = self.id

        name = self.name

        labels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels



        status = self.status

        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "id": id,
            "name": name,
        })
        if labels is not UNSET:
            field_dict["labels"] = labels
        if status is not UNSET:
            field_dict["status"] = status
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.detector_out_metadata import DetectorOutMetadata
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        labels = cast(list[str], d.pop("labels", UNSET))


        status = d.pop("status", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, DetectorOutMetadata]
        if isinstance(_metadata,  Unset):
            metadata = UNSET
        else:
            metadata = DetectorOutMetadata.from_dict(_metadata)




        detector_out = cls(
            id=id,
            name=name,
            labels=labels,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            metadata=metadata,
        )


        detector_out.additional_properties = d
        return detector_out

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
