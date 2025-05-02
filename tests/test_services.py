from pydantic import ValidationError
from pytest import fixture, raises

from database import db_connect
from pyfreeradius.models import AttributeOpValue, Group, GroupUser, Nas, User, UserGroup
from pyfreeradius.repositories import GroupRepository, NasRepository, UserRepository
from pyfreeradius.schemas import GroupUpdate, NasUpdate, UserUpdate
from pyfreeradius.services import GroupService, NasService, Result, ServiceError, UserService

#
# Each test will depend on services instance.
#


class Services:
    def __init__(self, user: UserService, group: GroupService, nas: NasService):
        self.user = user
        self.group = group
        self.nas = nas


@fixture
def services():
    db_session = db_connect()
    user_repo = UserRepository(db_session)
    group_repo = GroupRepository(db_session)
    nas_repo = NasRepository(db_session)
    try:
        yield Services(
            user=UserService(user_repo=user_repo, group_repo=group_repo),
            group=GroupService(group_repo=group_repo, user_repo=user_repo),
            nas=NasService(nas_repo=nas_repo),
        )
    except:
        # on any error, we rollback the DB
        db_session.rollback()
        raise
    else:
        # otherwise, we commit the DB
        db_session.commit()
    finally:
        # in any case, we close the DB session
        db_session.close()


#
# Some data reused across the tests.
#

nas1 = Nas(
    nasname="nas1.pyfreeradius",
    shortname="nas1-shortname",
    secret="nas1-secret",
)

user1 = User(
    username="user1.pyfreeradius",
    checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="password")],
    replies=[
        AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.1"),
        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24"),
        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24"),
        AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="my-vrf"),
    ],
)

group1 = Group(
    groupname="group1.pyfreeradius",
    checks=[AttributeOpValue(attribute="Auth-Type", op=":=", value="Accept")],
    replies=[AttributeOpValue(attribute="Filter-Id", op=":=", value="100m")],
)

#
# The tests.
#


def test_nas(services):
    result = services.nas.get(nasname=nas1.nasname)
    assert result.is_failure()
    assert result.error == ServiceError.NAS_NOT_FOUND  # NAS not found yet

    result = services.nas.get_all(from_nasname="nas1.pyfreeradiu")
    assert result.is_success()
    assert nas1 not in result.value  # NAS not part of collection yet

    result = services.nas.create(nas=nas1)
    assert result.is_success()
    assert result.value == nas1  # NAS created

    result = services.nas.create(nas=nas1)
    assert result.is_failure()
    assert result.error == ServiceError.NAS_ALREADY_EXISTS  # NAS already exists

    result = services.nas.get(nasname=nas1.nasname)
    assert result.is_success()
    assert result.value == nas1  # NAS now found

    result = services.nas.get_all(from_nasname="nas1.pyfreeradiu")
    assert result.is_success()
    assert nas1 in result.value  # NAS now part of collection

    result = services.nas.delete(nasname=nas1.nasname)
    assert result.is_success()  # NAS deleted
    assert result.value is None

    result = services.nas.delete(nasname=nas1.nasname)
    assert result.is_failure()
    assert result.error == ServiceError.NAS_NOT_FOUND  # NAS now not found


def test_user(services):
    result = services.user.get(username=user1.username)
    assert result.is_failure()
    assert result.error == ServiceError.USER_NOT_FOUND  # user not found yet

    result = services.user.get_all(from_username="user1.pyfreeradiu")
    assert result.is_success()
    assert user1 not in result.value  # user not part of collection yet

    result = services.user.create(user=user1)
    assert result.is_success()
    assert result.value == user1  # user created

    result = services.user.create(user=user1)
    assert result.is_failure()
    assert result.error == ServiceError.USER_ALREADY_EXISTS  # user already exists

    result = services.user.get(username=user1.username)
    assert result.is_success()
    assert result.value == user1  # user now found

    result = services.user.get_all(from_username="user1.pyfreeradiu")
    assert result.is_success()
    assert user1 in result.value  # user now part of collection

    result = services.user.delete(username=user1.username)
    assert result.is_success()  # user deleted
    assert result.value is None

    result = services.user.delete(username=user1.username)
    assert result.is_failure()
    assert result.error == ServiceError.USER_NOT_FOUND  # user now not found


def test_group(services):
    result = services.group.get(groupname=group1.groupname)
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_NOT_FOUND  # group not found yet

    result = services.group.get_all(from_groupname="group1.pyfreeradiu")
    assert result.is_success()
    assert group1 not in result.value  # group not part of collection yet

    result = services.group.create(group=group1)
    assert result.is_success()
    assert result.value == group1  # group created

    result = services.group.create(group=group1)
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_ALREADY_EXISTS  # group already exists

    result = services.group.get(groupname=group1.groupname)
    assert result.is_success()
    assert result.value == group1  # group now found

    result = services.group.get_all(from_groupname="group1.pyfreeradiu")
    assert result.is_success()
    assert group1 in result.value  # group now part of collection

    result = services.group.delete(groupname=group1.groupname)
    assert result.is_success()  # group deleted
    assert result.value is None

    result = services.group.delete(groupname=group1.groupname)
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_NOT_FOUND  # group now not found


def test_user_with_groups(services):
    user_with_groups = User(
        username=user1.username,
        groups=[
            UserGroup(groupname="group1.pyfreeradius"),
            UserGroup(groupname="group2.pyfreeradius"),
        ],
    )

    # we create group1 but NOT group2 on purpose
    result = services.group.create(group=group1)
    assert result.is_success()

    result = services.user.create(user=user_with_groups)
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_NOT_FOUND  # group2 not found

    result = services.user.create(user=user_with_groups, allow_groups_creation=True)
    assert result.is_success()
    assert result.value == user_with_groups  # user created (as well as group2)

    result = services.group.get(groupname=user_with_groups.groups[1].groupname)
    assert result.is_success()  # group2 now found

    result = services.user.delete(username=user_with_groups.username)
    assert result.is_failure()
    assert (
        result.error == ServiceError.GROUP_WOULD_BE_DELETED
    )  # group2 would be deleted as it has no attributes but only users

    result = services.user.delete(username=user_with_groups.username, prevent_groups_deletion=False)
    assert result.is_success()
    assert result.value is None  # user now deleted (as well as group2)

    result = services.group.get(groupname=user_with_groups.groups[1].groupname)
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_NOT_FOUND  # group2 now not found

    result = services.group.delete(groupname=group1.groupname)
    assert result.is_success()  # group1 deleted


def test_group_with_users(services):
    group_with_users = Group(
        groupname=group1.groupname,
        users=[
            GroupUser(username="user1.pyfreeradius"),
            GroupUser(username="user2.pyfreeradius"),
        ],
    )

    # we create user1 but NOT user2 on purpose
    result = services.user.create(user=user1)
    assert result.is_success()

    result = services.group.create(group=group_with_users)
    assert result.is_failure()
    assert result.error == ServiceError.USER_NOT_FOUND  # user2 not found

    result = services.group.create(group=group_with_users, allow_users_creation=True)
    assert result.is_success()
    assert result.value == group_with_users  # group created (as well as user2)

    result = services.user.get(username=group_with_users.users[1].username)
    assert result.is_success()  # user2 now found

    result = services.group.delete(groupname=group_with_users.groupname)
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_HAS_USERS  # group still has users

    result = services.group.delete(groupname=group_with_users.groupname, ignore_users=True)
    assert result.is_failure()
    assert (
        result.error == ServiceError.USER_WOULD_BE_DELETED
    )  # user2 would be deleted as it has no attributes but only groups

    result = services.group.delete(
        groupname=group_with_users.groupname, ignore_users=True, prevent_users_deletion=False
    )
    assert result.is_success()
    assert result.value is None  # group now deleted (as well as user2)

    result = services.user.get(username=group_with_users.users[1].username)
    assert result.is_failure()
    assert result.error == ServiceError.USER_NOT_FOUND  # user2 now not found

    result = services.user.delete(username=user1.username)
    assert result.is_success()  # user1 deleted


def test_nas_update(services):
    # first, we create the NAS to update
    result = services.nas.create(nas=nas1)
    assert result.is_success()
    assert result.value == nas1

    # then, we update the NAS
    nas_update = NasUpdate(shortname="new-shortname", secret="new-secret")
    result = services.nas.update(nasname=nas1.nasname, nas_update=nas_update)
    assert result.is_success()
    assert result.value == Nas(nasname=nas1.nasname, shortname=nas_update.shortname, secret=nas_update.secret)

    # delete NAS
    result = services.nas.delete(nasname=nas1.nasname)
    assert result.is_success()


def test_user_update(services):
    # first, we create the user to update

    result = services.user.create(user=user1)
    assert result.is_success()
    assert result.value == user1

    # only update check attributes, without changing reply attributes and groups

    user_update = UserUpdate(checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="new-password")])

    result = services.user.update(username=user1.username, user_update=user_update)
    assert result.is_success()
    assert result.value == User(username=user1.username, replies=user1.replies, checks=user_update.checks)

    # the user will have only check attributes

    user_update = UserUpdate(checks=user1.checks, replies=None, groups=None)

    result = services.user.update(username=user1.username, user_update=user_update)
    assert result.is_success()
    assert result.value == User(username=user1.username, checks=user1.checks, replies=[], groups=[])

    result = services.user.update(username=user1.username, user_update=UserUpdate(checks=[]))
    assert result.is_failure()
    assert result.error == ServiceError.USER_WOULD_BE_DELETED

    # the user will have only reply attributes

    user_update = UserUpdate(checks=[], replies=user1.replies, groups=[])  # [] similar to None as per RFC 7396

    result = services.user.update(username=user1.username, user_update=user_update)
    assert result.is_success()
    assert result.value == User(username=user1.username, checks=[], replies=user1.replies, groups=[])

    result = services.user.update(username=user1.username, user_update=UserUpdate(replies=[]))
    assert result.is_failure()
    assert result.error == ServiceError.USER_WOULD_BE_DELETED

    # the user will have only groups

    user_update = UserUpdate(checks=None, replies=[], groups=[UserGroup(groupname=group1.groupname)])

    result = services.user.update(username=user1.username, user_update=user_update)
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_NOT_FOUND

    result = services.user.update(username=user1.username, user_update=user_update, allow_groups_creation=True)
    assert result.is_success()
    assert result.value == User(username=user1.username, checks=[], replies=[], groups=user_update.groups)

    result = services.user.update(username=user1.username, user_update=UserUpdate(groups=[]))
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_WOULD_BE_DELETED

    result = services.user.update(
        username=user1.username, user_update=UserUpdate(groups=[]), prevent_groups_deletion=False
    )
    assert result.is_failure()
    assert result.error == ServiceError.USER_WOULD_BE_DELETED

    # delete user

    result = services.user.delete(username=user1.username, prevent_groups_deletion=False)
    assert result.is_success()


def test_group_update(services):
    # first, we create the group to update

    result = services.group.create(group=group1)
    assert result.is_success()
    assert result.value == group1

    # only update check attributes, without changing reply attributes and users

    group_update = GroupUpdate(checks=[AttributeOpValue(attribute="Auth-Type", op=":=", value="Reject")])

    result = services.group.update(groupname=group1.groupname, group_update=group_update)
    assert result.is_success()
    assert result.value == Group(groupname=group1.groupname, replies=group1.replies, checks=group_update.checks)

    # the group will have only check attributes

    group_update = GroupUpdate(checks=group1.checks, replies=None, users=None)

    result = services.group.update(groupname=group1.groupname, group_update=group_update)
    assert result.is_success()
    assert result.value == Group(groupname=group1.groupname, checks=group1.checks, replies=[], users=[])

    result = services.group.update(groupname=group1.groupname, group_update=GroupUpdate(checks=[]))
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_WOULD_BE_DELETED

    # the group will have only reply attributes

    group_update = GroupUpdate(checks=[], replies=group1.replies, users=[])  # [] similar to None as per RFC 7396

    result = services.group.update(groupname=group1.groupname, group_update=group_update)
    assert result.is_success()
    assert result.value == Group(groupname=group1.groupname, checks=[], replies=group1.replies, users=[])

    result = services.group.update(groupname=group1.groupname, group_update=GroupUpdate(replies=[]))
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_WOULD_BE_DELETED

    # the group will have only users

    group_update = GroupUpdate(checks=None, replies=[], users=[GroupUser(username=user1.username)])

    result = services.group.update(groupname=group1.groupname, group_update=group_update)
    assert result.is_failure()
    assert result.error == ServiceError.USER_NOT_FOUND

    result = services.group.update(groupname=group1.groupname, group_update=group_update, allow_users_creation=True)
    assert result.is_success()
    assert result.value == Group(groupname=group1.groupname, checks=[], replies=[], users=group_update.users)

    result = services.group.update(groupname=group1.groupname, group_update=GroupUpdate(users=[]))
    assert result.is_failure()
    assert result.error == ServiceError.USER_WOULD_BE_DELETED

    result = services.group.update(
        groupname=group1.groupname, group_update=GroupUpdate(users=[]), prevent_users_deletion=False
    )
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_WOULD_BE_DELETED

    # delete group

    result = services.group.delete(groupname=group1.groupname, ignore_users=True, prevent_users_deletion=False)
    assert result.is_success()


def test_nas_update_nonexistent(services):
    result = services.nas.update(nasname="nonexistent-nas", nas_update=NasUpdate())
    assert result.is_failure()
    assert result.error == ServiceError.NAS_NOT_FOUND


def test_user_update_nonexistent(services):
    result = services.user.update(username="nonexistent-user", user_update=UserUpdate())
    assert result.is_failure()
    assert result.error == ServiceError.USER_NOT_FOUND


def test_group_update_nonexistent(services):
    result = services.group.update(groupname="nonexistent-group", group_update=GroupUpdate())
    assert result.is_failure()
    assert result.error == ServiceError.GROUP_NOT_FOUND


def test_user_update_validation_error():
    with raises(ValidationError):
        # resulting user would have no attributes and no groups
        UserUpdate(checks=[], replies=[], groups=[])
    with raises(ValidationError):
        # given groups have one or more duplicates
        UserUpdate(groups=[UserGroup(groupname="not-unique"), UserGroup(groupname="not-unique")])


def test_group_update_validation_error():
    with raises(ValidationError):
        # resulting group would have no attributes and no users
        GroupUpdate(checks=[], replies=[], users=[])
    with raises(ValidationError):
        # given users have one or more duplicates
        GroupUpdate(users=[GroupUser(username="not-unique"), GroupUser(username="not-unique")])


def test_result_validation_error():
    with raises(ValidationError):
        # 'error' must be provided if 'error_detail' is set
        Result(error_detail="some info")
    with raises(ValidationError):
        # 'value' must not be provided if 'error' is set
        Result(error=ServiceError.USER_NOT_FOUND, value="some value")
