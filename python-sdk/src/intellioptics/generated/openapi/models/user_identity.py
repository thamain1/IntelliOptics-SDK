"""Authenticated user identity payload."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, List, Optional, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UserIdentity")


@_attrs_define
class UserIdentity:
    """Details returned by ``GET /v1/users/me``."""

    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    tenant: Optional[str] = None
    roles: List[str] = _attrs_field(factory=list)
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "id": self.id,
            "roles": list(self.roles),
        })
        if self.email is not None:
            field_dict["email"] = self.email
        if self.name is not None:
            field_dict["name"] = self.name
        if self.tenant is not None:
            field_dict["tenant"] = self.tenant
        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_identity = cls(
            id=d.pop("id"),
            email=d.pop("email", None),
            name=d.pop("name", None),
            tenant=d.pop("tenant", None),
            roles=list(d.pop("roles", [])),
        )
        user_identity.additional_properties = d
        return user_identity

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
