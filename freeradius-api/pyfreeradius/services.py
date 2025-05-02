from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, model_validator
from typing_extensions import Self

from .models import Group, Nas, User
from .repositories import GroupRepository, NasRepository, UserRepository
from .schemas import GroupUpdate, NasUpdate, UserUpdate

#
# Here we implement the Result pattern.
#
# Instead of raising exceptions for known domain errors,
# which will end up in exception-based control flow in upper layer,
# we return a result indicating either a success or a failure.
#
# In case of a success, the result carries the value (payload) to return.
# In case of a failure, the result carries the error type and info.
#


class ServiceError(str, Enum):
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_WOULD_BE_DELETED = "USER_WOULD_BE_DELETED"
    GROUP_ALREADY_EXISTS = "GROUP_ALREADY_EXISTS"
    GROUP_HAS_USERS = "GROUP_HAS_USERS"
    GROUP_NOT_FOUND = "GROUP_NOT_FOUND"
    GROUP_WOULD_BE_DELETED = "GROUP_WOULD_BE_DELETED"
    NAS_ALREADY_EXISTS = "NAS_ALREADY_EXISTS"
    NAS_NOT_FOUND = "NAS_NOT_FOUND"


T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    value: T | None = None
    error: ServiceError | None = None
    error_detail: str | None = None

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        if self.error_detail and not self.error:
            raise ValueError("'error' must be provided if 'error_detail' is set")
        if self.error and self.value:
            raise ValueError("'value' must not be provided if 'error' is set")
        return self

    def is_success(self) -> bool:
        return self.error is None

    def is_failure(self) -> bool:
        return not self.is_success()


#
# Services rely on the Repositories and implement the Domain logic.
# They then can be used by multiple Applications (API, CLI, etc.).
#


class UserService:
    def __init__(self, user_repo: UserRepository, group_repo: GroupRepository):
        self.user_repo = user_repo
        self.group_repo = group_repo

    def get(self, username: str) -> Result[User]:
        user = self.user_repo.find_one(username)
        if not user:
            return Result(error=ServiceError.USER_NOT_FOUND, error_detail="Given user does not exist")
        return Result(value=user)

    def get_all(self, from_username: str | None = None) -> Result[list[User]]:
        return Result(value=self.user_repo.find_all(from_username))

    def create(self, user: User, allow_groups_creation: bool = False) -> Result[User]:
        if self.user_repo.exists(user.username):
            return Result(error=ServiceError.USER_ALREADY_EXISTS, error_detail="Given user already exists")

        if not allow_groups_creation:
            for usergroup in user.groups:
                if not self.group_repo.exists(usergroup.groupname):
                    return Result(
                        error=ServiceError.GROUP_NOT_FOUND,
                        error_detail=f"Given group '{usergroup.groupname}' does not exist: "
                        "create it first or set 'allow_groups_creation' parameter to true",
                    )

        self.user_repo.add(user)
        return Result(value=user)

    def delete(self, username: str, prevent_groups_deletion: bool = True) -> Result[None]:
        user = self.user_repo.find_one(username)
        if not user:
            return Result(error=ServiceError.USER_NOT_FOUND, error_detail="Given user does not exist")

        if prevent_groups_deletion:
            for usergroup in user.groups:
                group = self.group_repo.find_one(usergroup.groupname)
                if group and not (group.checks or group.replies):
                    return Result(
                        error=ServiceError.GROUP_WOULD_BE_DELETED,
                        error_detail=f"Group '{group.groupname}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_groups_deletion' parameter to false",
                    )

        self.user_repo.remove(username)
        return Result(value=None)

    def update(
        self,
        username: str,
        user_update: UserUpdate,
        allow_groups_creation: bool = False,
        prevent_groups_deletion: bool = True,
    ) -> Result[User]:
        user = self.user_repo.find_one(username)
        if not user:
            return Result(error=ServiceError.USER_NOT_FOUND, error_detail="Given user does not exist")

        if user_update.groups:
            if not allow_groups_creation:
                for usergroup in user_update.groups:
                    if not self.group_repo.exists(usergroup.groupname):
                        return Result(
                            error=ServiceError.GROUP_NOT_FOUND,
                            error_detail=f"Given group '{usergroup.groupname}' does not exist: create it first"
                            "create it first or set 'allow_groups_creation' parameter to true",
                        )

        if (user_update.groups or user_update.groups == []) and prevent_groups_deletion:
            for usergroup in user.groups:
                group = self.group_repo.find_one(usergroup.groupname)
                if group and not (group.checks or group.replies):
                    return Result(
                        error=ServiceError.GROUP_WOULD_BE_DELETED,
                        error_detail=f"Group '{group.groupname}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_groups_deletion' parameter to false",
                    )

        new_checks = user.checks if user_update.checks is None else user_update.checks
        new_replies = user.replies if user_update.replies is None else user_update.replies
        new_groups = user.groups if user_update.groups is None else user_update.groups
        if not (new_checks or new_replies or new_groups):
            return Result(
                error=ServiceError.USER_WOULD_BE_DELETED,
                error_detail="Resulting user would have no attributes and no groups",
            )

        self.user_repo.set(
            username=username,
            new_checks=user_update.checks,
            new_replies=user_update.replies,
            new_groups=user_update.groups,
        )
        return Result(value=self.user_repo.find_one(username))


class GroupService:
    def __init__(self, group_repo: GroupRepository, user_repo: UserRepository):
        self.group_repo = group_repo
        self.user_repo = user_repo

    def get(self, groupname: str) -> Result[Group]:
        group = self.group_repo.find_one(groupname)
        if not group:
            return Result(error=ServiceError.GROUP_NOT_FOUND, error_detail="Given group does not exist")
        return Result(value=group)

    def get_all(self, from_groupname: str | None = None) -> Result[list[Group]]:
        return Result(value=self.group_repo.find_all(from_groupname))

    def create(self, group: Group, allow_users_creation: bool = False) -> Result[Group]:
        if self.group_repo.exists(group.groupname):
            return Result(error=ServiceError.GROUP_ALREADY_EXISTS, error_detail="Given group already exists")

        if not allow_users_creation:
            for groupuser in group.users:
                if not self.user_repo.exists(groupuser.username):
                    return Result(
                        error=ServiceError.USER_NOT_FOUND,
                        error_detail=f"Given user '{groupuser.username}' does not exist: "
                        "create it first or set 'allow_users_creation' parameter to true",
                    )

        self.group_repo.add(group)
        return Result(value=group)

    def delete(self, groupname: str, ignore_users: bool = False, prevent_users_deletion: bool = True) -> Result[None]:
        group = self.group_repo.find_one(groupname)
        if not group:
            return Result(error=ServiceError.GROUP_NOT_FOUND, error_detail="Given group does not exist")

        if group.users and not ignore_users:
            return Result(
                error=ServiceError.GROUP_HAS_USERS,
                error_detail="Given group has users: delete them first or set 'ignore_users' parameter to true",
            )

        if prevent_users_deletion:
            for groupuser in group.users:
                user = self.user_repo.find_one(groupuser.username)
                if user and not (user.checks or user.replies):
                    return Result(
                        error=ServiceError.USER_WOULD_BE_DELETED,
                        error_detail=f"User '{user.username}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_users_deletion' parameter to false",
                    )

        self.group_repo.remove(groupname)
        return Result(value=None)

    def update(
        self,
        groupname: str,
        group_update: GroupUpdate,
        allow_users_creation: bool = False,
        prevent_users_deletion: bool = True,
    ) -> Result[Group]:
        group = self.group_repo.find_one(groupname)
        if not group:
            return Result(error=ServiceError.GROUP_NOT_FOUND, error_detail="Given group does not exist")

        if group_update.users:
            if not allow_users_creation:
                for groupuser in group_update.users:
                    if not self.user_repo.exists(groupuser.username):
                        return Result(
                            error=ServiceError.USER_NOT_FOUND,
                            error_detail=f"Given user '{groupuser.username}' does not exist: create it first"
                            "create it first or set 'allow_users_creation' parameter to true",
                        )

        if (group_update.users or group_update.users == []) and prevent_users_deletion:
            for groupuser in group.users:
                user = self.user_repo.find_one(groupuser.username)
                if user and not (user.checks or user.replies):
                    return Result(
                        error=ServiceError.USER_WOULD_BE_DELETED,
                        error_detail=f"User '{user.username}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_users_deletion' parameter to false",
                    )

        new_checks = group.checks if group_update.checks is None else group_update.checks
        new_replies = group.replies if group_update.replies is None else group_update.replies
        new_users = group.users if group_update.users is None else group_update.users
        if not (new_checks or new_replies or new_users):
            return Result(
                error=ServiceError.GROUP_WOULD_BE_DELETED,
                error_detail="Resulting group would have no attributes and no users",
            )

        self.group_repo.set(
            groupname=groupname,
            new_checks=group_update.checks,
            new_replies=group_update.replies,
            new_users=group_update.users,
        )
        return Result(value=self.group_repo.find_one(groupname))


class NasService:
    def __init__(self, nas_repo: NasRepository):
        self.nas_repo = nas_repo

    def get(self, nasname: str) -> Result[Nas]:
        nas = self.nas_repo.find_one(nasname)
        if not nas:
            return Result(error=ServiceError.NAS_NOT_FOUND, error_detail="Given NAS does not exist")
        return Result(value=nas)

    def get_all(self, from_nasname: str | None = None) -> Result[list[Nas]]:
        return Result(value=self.nas_repo.find_all(from_nasname))

    def create(self, nas: Nas) -> Result[Nas]:
        if self.nas_repo.exists(nas.nasname):
            return Result(error=ServiceError.NAS_ALREADY_EXISTS, error_detail="Given NAS already exists")
        self.nas_repo.add(nas)
        return Result(value=nas)

    def delete(self, nasname: str) -> Result[None]:
        if not self.nas_repo.exists(nasname):
            return Result(error=ServiceError.NAS_NOT_FOUND, error_detail="Given NAS does not exist")
        self.nas_repo.remove(nasname)
        return Result(value=None)

    def update(self, nasname: str, nas_update: NasUpdate) -> Result[Nas]:
        nas = self.nas_repo.find_one(nasname)
        if not nas:
            return Result(error=ServiceError.NAS_NOT_FOUND, error_detail="Given NAS does not exist")
        self.nas_repo.set(nasname, new_shortname=nas_update.shortname, new_secret=nas_update.secret)
        return Result(value=self.nas_repo.find_one(nasname))
