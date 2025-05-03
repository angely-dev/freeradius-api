from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

#
# The Pydantic models implement the UML class diagram;
# it is NOT a one-to-one mapping with database tables.
#
# The association between User and Group is implemented
# with two models (one for each direction).
#


class AttributeOpValue(BaseModel):
    attribute: Annotated[str, StringConstraints(min_length=1)]
    op: Annotated[str, StringConstraints(min_length=1)]
    value: Annotated[str, StringConstraints(min_length=1)]

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }


class UserGroup(BaseModel):
    groupname: Annotated[str, StringConstraints(min_length=1)]
    priority: Annotated[int, Field(ge=1)] = 1

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }


class GroupUser(BaseModel):
    username: Annotated[str, StringConstraints(min_length=1)]
    priority: Annotated[int, Field(ge=1)] = 1

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }


class User(BaseModel):
    username: Annotated[str, StringConstraints(min_length=1)]
    checks: list[AttributeOpValue] = []
    replies: list[AttributeOpValue] = []
    groups: list[UserGroup] = []

    @model_validator(mode="after")
    def check_fields_on_init(self):
        if not (self.checks or self.replies or self.groups):
            raise ValueError(
                "User must have at least one check or one reply attribute, or must have at least one group"
            )

        groupnames = [group.groupname for group in self.groups]
        if not len(groupnames) == len(set(groupnames)):
            raise ValueError("Given groups have one or more duplicates")

        return self

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "json_schema_extra": {
            "examples": [
                {
                    "username": "my-user",
                    "checks": [AttributeOpValue(attribute="Cleartext-Password", op=":=", value="my-pass").model_dump()],
                    "replies": [
                        AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.1").model_dump(),
                        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24").model_dump(),
                        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24").model_dump(),
                        AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="my-vrf").model_dump(),
                    ],
                    "groups": [UserGroup(groupname="my-group").model_dump()],
                }
            ]
        },
    }


class Group(BaseModel):
    groupname: Annotated[str, StringConstraints(min_length=1)]
    checks: list[AttributeOpValue] = []
    replies: list[AttributeOpValue] = []
    users: list[GroupUser] = []

    @model_validator(mode="after")
    def check_fields_on_init(self):
        if not (self.checks or self.replies or self.users):
            raise ValueError(
                "Group must have at least one check or one reply attribute, or must have at least one user"
            )

        usernames = [user.username for user in self.users]
        if not len(usernames) == len(set(usernames)):
            raise ValueError("Given users have one or more duplicates")

        return self

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "json_schema_extra": {
            "examples": [
                {
                    "groupname": "my-group",
                    "replies": [AttributeOpValue(attribute="Filter-Id", op=":=", value="10m").model_dump()],
                }
            ]
        },
    }


class Nas(BaseModel):
    nasname: Annotated[str, StringConstraints(min_length=1)]
    shortname: Annotated[str, StringConstraints(min_length=1)]
    secret: Annotated[str, StringConstraints(min_length=1)]

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "json_schema_extra": {"examples": [{"nasname": "5.5.5.5", "shortname": "my-nas", "secret": "my-secret"}]},
    }
