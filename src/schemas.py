from pydantic import BaseModel, StringConstraints
from pyfreeradius.models import AttributeOpValue, UserGroup, GroupUser, model_validator
from typing import Annotated


class UserUpdate(BaseModel):
    checks: list[AttributeOpValue] | None = None
    replies: list[AttributeOpValue] | None = None
    groups: list[UserGroup] | None = None

    @model_validator(mode="after")
    def check_fields_on_init(self):
        if self.checks == [] and self.replies == [] and self.groups == []:
            raise ValueError("Resulting user would have no attributes and no groups")

        groupnames = [group.groupname for group in self.groups or []]
        if not len(groupnames) == len(set(groupnames)):
            raise ValueError("Given groups have one or more duplicates")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"checks": [AttributeOpValue(attribute="Cleartext-Password", op=":=", value="new-pass").model_dump()]}
            ]
        }
    }


class GroupUpdate(BaseModel):
    checks: list[AttributeOpValue] | None = None
    replies: list[AttributeOpValue] | None = None
    users: list[GroupUser] | None = None

    @model_validator(mode="after")
    def check_fields_on_init(self):
        if self.checks == [] and self.replies == []:
            raise ValueError("Resulting group would have no attributes")

        usernames = [user.username for user in self.users or []]
        if not len(usernames) == len(set(usernames)):
            raise ValueError("Given users have one or more duplicates")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "replies": [AttributeOpValue(attribute="Filter-Id", op=":=", value="20m").model_dump()],
                }
            ]
        }
    }


class NasUpdate(BaseModel):
    shortname: Annotated[str, StringConstraints(min_length=1)] | None = None
    secret: Annotated[str, StringConstraints(min_length=1)] | None = None

    model_config = {"json_schema_extra": {"examples": [{"shortname": "new-shortname", "secret": "new-secret"}]}}
