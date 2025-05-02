from pydantic import ValidationError
from pytest import fixture, raises

from database import db_connect
from pyfreeradius.models import AttributeOpValue, Group, GroupUser, Nas, User, UserGroup
from pyfreeradius.repositories import GroupRepository, NasRepository, UserRepository
from pyfreeradius.schemas import GroupUpdate, NasUpdate, UserUpdate
from pyfreeradius.services import GroupService, NasService, ServiceExceptions, UserService

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
    with raises(ServiceExceptions.NasNotFound):
        # NAS not found yet
        services.nas.get(nasname=nas1.nasname)
    assert nas1 not in services.nas.get_all(from_nasname="nas1.pyfreeradiu")  # NAS not part of collection yet

    services.nas.create(nas=nas1)  # NAS created
    with raises(ServiceExceptions.NasAlreadyExists):
        # NAS already exists
        services.nas.create(nas=nas1)

    assert nas1 == services.nas.get(nasname=nas1.nasname)  # NAS now found
    assert nas1 in services.nas.get_all(from_nasname="nas1.pyfreeradiu")  # NAS now part of collection

    services.nas.delete(nasname=nas1.nasname)  # NAS deleted
    with raises(ServiceExceptions.NasNotFound):
        # NAS now not found
        services.nas.delete(nasname=nas1.nasname)


def test_user(services):
    with raises(ServiceExceptions.UserNotFound):
        # user not found yet
        services.user.get(username=user1.username)
    assert user1 not in services.user.get_all(from_username="user1.pyfreeradiu")  # user not part of collection yet

    services.user.create(user=user1)  # user created
    with raises(ServiceExceptions.UserAlreadyExists):
        # user already exists
        services.user.create(user=user1)

    assert user1 == services.user.get(username=user1.username)  # user now found
    assert user1 in services.user.get_all(from_username="user1.pyfreeradiu")  # user now part of collection

    services.user.delete(username=user1.username)  # user deleted
    with raises(ServiceExceptions.UserNotFound):
        # user now not found
        services.user.delete(username=user1.username)


def test_group(services):
    with raises(ServiceExceptions.GroupNotFound):
        # group not found yet
        services.group.get(groupname=group1.groupname)
    assert group1 not in services.group.get_all(from_groupname="group1.pyfreeradiu")  # group not part of collection yet

    services.group.create(group=group1)  # group created
    with raises(ServiceExceptions.GroupAlreadyExists):
        # group already exists
        services.group.create(group=group1)

    assert group1 == services.group.get(groupname=group1.groupname)  # group now found
    assert group1 in services.group.get_all(from_groupname="group1.pyfreeradiu")  # group now part of collection

    services.group.delete(groupname=group1.groupname)  # group deleted
    with raises(ServiceExceptions.GroupNotFound):
        # group now not found
        services.group.delete(groupname=group1.groupname)


def test_user_with_groups(services):
    user_with_groups = User(
        username=user1.username,
        groups=[
            UserGroup(groupname="group1.pyfreeradius"),
            UserGroup(groupname="group2.pyfreeradius"),
        ],
    )

    # we create group1 but NOT group2 on purpose
    services.group.create(group=group1)

    with raises(ServiceExceptions.GroupNotFound):
        # group2 not found
        services.user.create(user=user_with_groups)

    services.user.create(user=user_with_groups, allow_groups_creation=True)  # user created (as well as group2)
    assert services.group.get(groupname=user_with_groups.groups[1].groupname) == Group(
        groupname=user_with_groups.groups[1].groupname,
        users=[GroupUser(username=user_with_groups.username)],
    )  # group2 now found

    with raises(ServiceExceptions.GroupWouldBeDeleted):
        # group2 would be deleted as it has no attributes but only users
        services.user.delete(username=user_with_groups.username)

    services.user.delete(
        username=user_with_groups.username, prevent_groups_deletion=False
    )  # user now deleted (as well as group2)

    with raises(ServiceExceptions.GroupNotFound):
        # group2 now not found
        services.group.get(groupname=user_with_groups.groups[1].groupname)

    services.group.delete(groupname=group1.groupname)  # group1 deleted


def test_group_with_users(services):
    group_with_users = Group(
        groupname=group1.groupname,
        users=[
            GroupUser(username="user1.pyfreeradius"),
            GroupUser(username="user2.pyfreeradius"),
        ],
    )

    # we create user1 but NOT user2 on purpose
    services.user.create(user=user1)

    with raises(ServiceExceptions.UserNotFound):
        # user2 not found
        services.group.create(group=group_with_users)

    services.group.create(group=group_with_users, allow_users_creation=True)  # group created (as well as user2)
    assert services.user.get(username=group_with_users.users[1].username) == User(
        username=group_with_users.users[1].username,
        groups=[UserGroup(groupname=group_with_users.groupname)],
    )  # user2 now found

    with raises(ServiceExceptions.GroupStillHasUsers):
        # group still has users
        services.group.delete(groupname=group_with_users.groupname)

    with raises(ServiceExceptions.UserWouldBeDeleted):
        # user2 would be deleted as it has no attributes but only groups
        services.group.delete(groupname=group_with_users.groupname, ignore_users=True)

    services.group.delete(
        groupname=group_with_users.groupname, ignore_users=True, prevent_users_deletion=False
    )  # group now deleted (as well as user2)

    with raises(ServiceExceptions.UserNotFound):
        # user2 now not found
        services.user.get(username=group_with_users.users[1].username)

    services.user.delete(username=user1.username)  # user1 deleted


def test_nas_update(services):
    # first, we create the NAS to update
    services.nas.create(nas=nas1)

    # then, we update the NAS
    nas_update = NasUpdate(shortname="new-shortname", secret="new-secret")
    updated_nas = services.nas.update(nasname=nas1.nasname, nas_update=nas_update)
    assert updated_nas == Nas(nasname=nas1.nasname, shortname=nas_update.shortname, secret=nas_update.secret)

    # delete NAS
    services.nas.delete(nasname=nas1.nasname)


def test_user_update(services):
    # first, we create the user to update

    services.user.create(user=user1)

    # only update check attributes, without changing reply attributes and groups

    user_update = UserUpdate(checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="new-password")])

    updated_user = services.user.update(username=user1.username, user_update=user_update)
    assert updated_user == User(username=user1.username, replies=user1.replies, checks=user_update.checks)

    # the user will have only check attributes

    user_update = UserUpdate(checks=user1.checks, replies=None, groups=None)

    updated_user = services.user.update(username=user1.username, user_update=user_update)
    assert updated_user == User(username=user1.username, checks=user1.checks, replies=[], groups=[])

    with raises(ServiceExceptions.UserWouldBeDeleted):
        services.user.update(username=user1.username, user_update=UserUpdate(checks=[]))

    # the user will have only reply attributes

    user_update = UserUpdate(checks=[], replies=user1.replies, groups=[])  # [] similar to None as per RFC 7396

    updated_user = services.user.update(username=user1.username, user_update=user_update)
    assert updated_user == User(username=user1.username, checks=[], replies=user1.replies, groups=[])

    with raises(ServiceExceptions.UserWouldBeDeleted):
        services.user.update(username=user1.username, user_update=UserUpdate(replies=[]))

    # the user will have only groups

    user_update = UserUpdate(checks=None, replies=[], groups=[UserGroup(groupname=group1.groupname)])

    with raises(ServiceExceptions.GroupNotFound):
        services.user.update(username=user1.username, user_update=user_update)

    updated_user = services.user.update(username=user1.username, user_update=user_update, allow_groups_creation=True)
    assert updated_user == User(username=user1.username, checks=[], replies=[], groups=user_update.groups)

    with raises(ServiceExceptions.GroupWouldBeDeleted):
        services.user.update(username=user1.username, user_update=UserUpdate(groups=[]))

    with raises(ServiceExceptions.UserWouldBeDeleted):
        services.user.update(username=user1.username, user_update=UserUpdate(groups=[]), prevent_groups_deletion=False)

    # delete user

    services.user.delete(username=user1.username, prevent_groups_deletion=False)


def test_group_update(services):
    # first, we create the group to update

    services.group.create(group=group1)

    # only update check attributes, without changing reply attributes and users

    group_update = GroupUpdate(checks=[AttributeOpValue(attribute="Auth-Type", op=":=", value="Reject")])

    updated_group = services.group.update(groupname=group1.groupname, group_update=group_update)
    assert updated_group == Group(groupname=group1.groupname, replies=group1.replies, checks=group_update.checks)

    # the group will have only check attributes

    group_update = GroupUpdate(checks=group1.checks, replies=None, users=None)

    updated_group = services.group.update(groupname=group1.groupname, group_update=group_update)
    assert updated_group == Group(groupname=group1.groupname, checks=group1.checks, replies=[], users=[])

    with raises(ServiceExceptions.GroupWouldBeDeleted):
        services.group.update(groupname=group1.groupname, group_update=GroupUpdate(checks=[]))

    # the group will have only reply attributes

    group_update = GroupUpdate(checks=[], replies=group1.replies, users=[])  # [] similar to None as per RFC 7396

    updated_group = services.group.update(groupname=group1.groupname, group_update=group_update)
    assert updated_group == Group(groupname=group1.groupname, checks=[], replies=group1.replies, users=[])

    with raises(ServiceExceptions.GroupWouldBeDeleted):
        services.group.update(groupname=group1.groupname, group_update=GroupUpdate(replies=[]))

    # the group will have only users

    group_update = GroupUpdate(checks=None, replies=[], users=[GroupUser(username=user1.username)])

    with raises(ServiceExceptions.UserNotFound):
        services.group.update(groupname=group1.groupname, group_update=group_update)

    updated_group = services.group.update(
        groupname=group1.groupname, group_update=group_update, allow_users_creation=True
    )
    assert updated_group == Group(groupname=group1.groupname, checks=[], replies=[], users=group_update.users)

    with raises(ServiceExceptions.UserWouldBeDeleted):
        services.group.update(groupname=group1.groupname, group_update=GroupUpdate(users=[]))

    with raises(ServiceExceptions.GroupWouldBeDeleted):
        services.group.update(
            groupname=group1.groupname, group_update=GroupUpdate(users=[]), prevent_users_deletion=False
        )

    # delete group

    services.group.delete(groupname=group1.groupname, ignore_users=True, prevent_users_deletion=False)


def test_nas_update_nonexistent(services):
    with raises(ServiceExceptions.NasNotFound):
        services.nas.update(nasname="nonexistent-nas", nas_update=NasUpdate())


def test_user_update_nonexistent(services):
    with raises(ServiceExceptions.UserNotFound):
        services.user.update(username="nonexistent-user", user_update=UserUpdate())


def test_group_update_nonexistent(services):
    with raises(ServiceExceptions.GroupNotFound):
        services.group.update(groupname="nonexistent-group", group_update=GroupUpdate())


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
