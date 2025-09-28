
from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

"""Authenticated user identity payload."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, List, Optional, TypeVar

from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast


from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset
from ..types import UNSET, Unset
from typing import cast, Union
from typing import Union

from ..types import UNSET, Unset


T = TypeVar("T", bound="UserIdentity")


@_attrs_define
class UserIdentity:
    """
        Attributes:
            id (str):
            email (Union[None, Unset, str]):
            name (Union[None, Unset, str]):
            tenant (Union[None, Unset, str]):
            roles (Union[Unset, list[str]]):


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

    """
    Attributes:
        id (str):
        email (Union[None, Unset, str]):
        name (Union[None, Unset, str]):
        tenant (Union[None, Unset, str]):
        roles (Union[Unset, list[str]]):

    """

    id: str
    email: Union[None, Unset, str] = UNSET
    name: Union[None, Unset, str] = UNSET
    tenant: Union[None, Unset, str] = UNSET
    roles: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        email: Union[None, Unset, str]
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        tenant: Union[None, Unset, str]
        if isinstance(self.tenant, Unset):
            tenant = UNSET
        else:
            tenant = self.tenant


        roles: Union[Unset, list[str]]
        if isinstance(self.roles, Unset):
            roles = UNSET
        else:

        roles: Union[Unset, list[str]] = UNSET
        if not isinstance(self.roles, Unset):

            roles = self.roles

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        field_dict.update({
            "id": id,
        })

        field_dict.update(
            {
                "id": id,
            }
        )

        if email is not UNSET:
            field_dict["email"] = email
        if name is not UNSET:
            field_dict["name"] = name
        if tenant is not UNSET:
            field_dict["tenant"] = tenant
        if roles is not UNSET:
            field_dict["roles"] = roles

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


        id = d.pop("id")

        def _parse_email(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_tenant(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tenant = _parse_tenant(d.pop("tenant", UNSET))


        def _parse_roles(data: object) -> Union[Unset, list[str]]:
            if isinstance(data, Unset):
                return data
            if isinstance(data, list):
                return cast(Union[Unset, list[str]], data)
            return cast(Union[Unset, list[str]], data)

        roles = _parse_roles(d.pop("roles", UNSET))

        roles = cast(list[str], d.pop("roles", UNSET))

        user_identity = cls(
            id=id,
            email=email,
            name=name,
            tenant=tenant,
            roles=roles,
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
