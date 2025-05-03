from typing import Annotated

from pydantic import BaseModel, StringConstraints, model_validator

from pyfreeradius.models import AttributeOpValue, GroupUser, UserGroup

#
# These are "complex" parameters used by update methods in services.
# They allow partial update (aka PATCH) of a user, a group or a NAS.
#


class UserUpdate(BaseModel):
    checks: list[AttributeOpValue] | None = None
    replies: list[AttributeOpValue] | None = None
    groups: list[UserGroup] | None = None

    @model_validator(mode="after")
    def check_fields_on_init(self):
        # As per RFC 7396 (JSON Merge Patch), "null" value (i.e., "None" in Python) means removal.
        # We consider "null" to be the same as "[]" (empty list), it will ease further processing.
        provided_fields = self.model_dump(exclude_unset=True)
        if "checks" in provided_fields and self.checks is None:
            self.checks = []
        if "replies" in provided_fields and self.replies is None:
            self.replies = []
        if "groups" in provided_fields and self.groups is None:
            self.groups = []

        if self.checks == [] and self.replies == [] and self.groups == []:
            raise ValueError("Resulting user would have no attributes and no groups")

        groupnames = [group.groupname for group in self.groups or []]
        if not len(groupnames) == len(set(groupnames)):
            raise ValueError("Given groups have one or more duplicates")

        return self

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "json_schema_extra": {
            "examples": [
                {"checks": [AttributeOpValue(attribute="Cleartext-Password", op=":=", value="new-pass").model_dump()]}
            ]
        },
    }


class GroupUpdate(BaseModel):
    checks: list[AttributeOpValue] | None = None
    replies: list[AttributeOpValue] | None = None
    users: list[GroupUser] | None = None

    @model_validator(mode="after")
    def check_fields_on_init(self):
        # As per RFC 7396 (JSON Merge Patch), "null" value (i.e., "None" in Python) means removal.
        # We consider "null" to be the same as "[]" (empty list), it will ease further processing.
        provided_fields = self.model_dump(exclude_unset=True)
        if "checks" in provided_fields and self.checks is None:
            self.checks = []
        if "replies" in provided_fields and self.replies is None:
            self.replies = []
        if "users" in provided_fields and self.users is None:
            self.users = []

        if self.checks == [] and self.replies == [] and self.users == []:
            raise ValueError("Resulting group would have no attributes and no users")

        usernames = [user.username for user in self.users or []]
        if not len(usernames) == len(set(usernames)):
            raise ValueError("Given users have one or more duplicates")

        return self

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "json_schema_extra": {
            "examples": [
                {
                    "replies": [AttributeOpValue(attribute="Filter-Id", op=":=", value="20m").model_dump()],
                }
            ]
        },
    }


class NasUpdate(BaseModel):
    shortname: Annotated[str, StringConstraints(min_length=1)] | None = None
    secret: Annotated[str, StringConstraints(min_length=1)] | None = None

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "json_schema_extra": {"examples": [{"shortname": "new-shortname", "secret": "new-secret"}]},
    }
