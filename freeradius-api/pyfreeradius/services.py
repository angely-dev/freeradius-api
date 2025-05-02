from .models import Group, Nas, User
from .params import GroupUpdate, NasUpdate, UserUpdate
from .repositories import GroupRepository, NasRepository, UserRepository

#
# All possible domain errors.
#
# A previous version has experimented with the Result Pattern in
# order to prevent exception-based control flow in upper layers.
#
# This project being rather simple, and proposed as a package,
# I ended up preferring exceptions to convey domain errors,
# (this somewhat forces upper layers to catch or prevent them).
#


class ServiceExceptions:
    class UserNotFound(Exception):
        pass

    class GroupNotFound(Exception):
        pass

    class NasNotFound(Exception):
        pass

    class UserAlreadyExists(Exception):
        pass

    class GroupAlreadyExists(Exception):
        pass

    class NasAlreadyExists(Exception):
        pass

    class UserWouldBeDeleted(Exception):
        pass

    class GroupWouldBeDeleted(Exception):
        pass

    class GroupStillHasUsers(Exception):
        pass


#
# Services rely on the Repositories and implement the Domain logic.
# They then can be used by multiple Applications (API, CLI, etc.).
#


class UserService:
    def __init__(self, user_repo: UserRepository, group_repo: GroupRepository):
        self.user_repo = user_repo
        self.group_repo = group_repo

    def get(self, username: str) -> User:
        user = self.user_repo.find_one(username)
        if not user:
            raise ServiceExceptions.UserNotFound("Given user does not exist")
        return user

    def find_all(self, from_username: str | None = None) -> list[User]:
        return self.user_repo.find_all(from_username)

    def create(self, user: User, allow_groups_creation: bool = False) -> User:
        if self.user_repo.exists(user.username):
            raise ServiceExceptions.UserAlreadyExists("Given user already exists")

        if not allow_groups_creation:
            for usergroup in user.groups:
                if not self.group_repo.exists(usergroup.groupname):
                    raise ServiceExceptions.GroupNotFound(
                        f"Given group '{usergroup.groupname}' does not exist: "
                        "create it first or set 'allow_groups_creation' parameter to true",
                    )

        self.user_repo.add(user)
        return user

    def delete(self, username: str, prevent_groups_deletion: bool = True):
        user = self.user_repo.find_one(username)
        if not user:
            raise ServiceExceptions.UserNotFound("Given user does not exist")

        if prevent_groups_deletion:
            for usergroup in user.groups:
                group = self.group_repo.find_one(usergroup.groupname)
                if group and not (group.checks or group.replies):
                    raise ServiceExceptions.GroupWouldBeDeleted(
                        f"Group '{group.groupname}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_groups_deletion' parameter to false",
                    )

        self.user_repo.remove(username)

    def update(
        self,
        username: str,
        user_update: UserUpdate,
        allow_groups_creation: bool = False,
        prevent_groups_deletion: bool = True,
    ) -> User:
        user = self.user_repo.find_one(username)
        if not user:
            raise ServiceExceptions.UserNotFound("Given user does not exist")

        if user_update.groups:
            if not allow_groups_creation:
                for usergroup in user_update.groups:
                    if not self.group_repo.exists(usergroup.groupname):
                        raise ServiceExceptions.GroupNotFound(
                            f"Given group '{usergroup.groupname}' does not exist: "
                            "create it first or set 'allow_groups_creation' parameter to true",
                        )

        if (user_update.groups or user_update.groups == []) and prevent_groups_deletion:
            for usergroup in user.groups:
                group = self.group_repo.find_one(usergroup.groupname)
                if group and not (group.checks or group.replies):
                    raise ServiceExceptions.GroupWouldBeDeleted(
                        f"Group '{group.groupname}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_groups_deletion' parameter to false",
                    )

        new_checks = user.checks if user_update.checks is None else user_update.checks
        new_replies = user.replies if user_update.replies is None else user_update.replies
        new_groups = user.groups if user_update.groups is None else user_update.groups
        if not (new_checks or new_replies or new_groups):
            raise ServiceExceptions.UserWouldBeDeleted("Resulting user would have no attributes and no groups")

        self.user_repo.set(
            username=username,
            new_checks=user_update.checks,
            new_replies=user_update.replies,
            new_groups=user_update.groups,
        )
        return self.user_repo.find_one(username)  # type: ignore


class GroupService:
    def __init__(self, group_repo: GroupRepository, user_repo: UserRepository):
        self.group_repo = group_repo
        self.user_repo = user_repo

    def get(self, groupname: str) -> Group:
        group = self.group_repo.find_one(groupname)
        if not group:
            raise ServiceExceptions.GroupNotFound("Given group does not exist")
        return group

    def find_all(self, from_groupname: str | None = None) -> list[Group]:
        return self.group_repo.find_all(from_groupname)

    def create(self, group: Group, allow_users_creation: bool = False) -> Group:
        if self.group_repo.exists(group.groupname):
            raise ServiceExceptions.GroupAlreadyExists("Given group already exists")

        if not allow_users_creation:
            for groupuser in group.users:
                if not self.user_repo.exists(groupuser.username):
                    raise ServiceExceptions.UserNotFound(
                        f"Given user '{groupuser.username}' does not exist: "
                        "create it first or set 'allow_users_creation' parameter to true",
                    )

        self.group_repo.add(group)
        return group

    def delete(self, groupname: str, ignore_users: bool = False, prevent_users_deletion: bool = True):
        group = self.group_repo.find_one(groupname)
        if not group:
            raise ServiceExceptions.GroupNotFound("Given group does not exist")

        if group.users and not ignore_users:
            raise ServiceExceptions.GroupStillHasUsers(
                "Given group has users: delete them first or set 'ignore_users' parameter to true"
            )

        if prevent_users_deletion:
            for groupuser in group.users:
                user = self.user_repo.find_one(groupuser.username)
                if user and not (user.checks or user.replies):
                    raise ServiceExceptions.UserWouldBeDeleted(
                        f"User '{user.username}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_users_deletion' parameter to false",
                    )

        self.group_repo.remove(groupname)

    def update(
        self,
        groupname: str,
        group_update: GroupUpdate,
        allow_users_creation: bool = False,
        prevent_users_deletion: bool = True,
    ) -> Group:
        group = self.group_repo.find_one(groupname)
        if not group:
            raise ServiceExceptions.GroupNotFound("Given group does not exist")

        if group_update.users:
            if not allow_users_creation:
                for groupuser in group_update.users:
                    if not self.user_repo.exists(groupuser.username):
                        raise ServiceExceptions.UserNotFound(
                            f"Given user '{groupuser.username}' does not exist: "
                            "create it first or set 'allow_users_creation' parameter to true",
                        )

        if (group_update.users or group_update.users == []) and prevent_users_deletion:
            for groupuser in group.users:
                user = self.user_repo.find_one(groupuser.username)
                if user and not (user.checks or user.replies):
                    raise ServiceExceptions.UserWouldBeDeleted(
                        f"User '{user.username}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_users_deletion' parameter to false",
                    )

        new_checks = group.checks if group_update.checks is None else group_update.checks
        new_replies = group.replies if group_update.replies is None else group_update.replies
        new_users = group.users if group_update.users is None else group_update.users
        if not (new_checks or new_replies or new_users):
            raise ServiceExceptions.GroupWouldBeDeleted("Resulting group would have no attributes and no users")

        self.group_repo.set(
            groupname=groupname,
            new_checks=group_update.checks,
            new_replies=group_update.replies,
            new_users=group_update.users,
        )
        return self.group_repo.find_one(groupname)  # type: ignore


class NasService:
    def __init__(self, nas_repo: NasRepository):
        self.nas_repo = nas_repo

    def get(self, nasname: str) -> Nas:
        nas = self.nas_repo.find_one(nasname)
        if not nas:
            raise ServiceExceptions.NasNotFound("Given NAS does not exist")
        return nas

    def find_all(self, from_nasname: str | None = None) -> list[Nas]:
        return self.nas_repo.find_all(from_nasname)

    def create(self, nas: Nas) -> Nas:
        if self.nas_repo.exists(nas.nasname):
            raise ServiceExceptions.NasAlreadyExists("Given NAS already exists")
        self.nas_repo.add(nas)
        return nas

    def delete(self, nasname: str):
        if not self.nas_repo.exists(nasname):
            raise ServiceExceptions.NasNotFound("Given NAS does not exist")
        self.nas_repo.remove(nasname)

    def update(self, nasname: str, nas_update: NasUpdate) -> Nas:
        nas = self.nas_repo.find_one(nasname)
        if not nas:
            raise ServiceExceptions.NasNotFound("Given NAS does not exist")
        self.nas_repo.set(nasname, new_shortname=nas_update.shortname, new_secret=nas_update.secret)
        return self.nas_repo.find_one(nasname)  # type: ignore
