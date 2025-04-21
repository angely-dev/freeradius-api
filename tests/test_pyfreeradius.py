from pydantic import ValidationError
from pytest import fixture, raises

from database import db_connect
from pyfreeradius.models import AttributeOpValue, Group, GroupUser, Nas, User, UserGroup
from pyfreeradius.repositories import GroupRepository, NasRepository, UserRepository

#
# Each test will depend on repositories instance.
#


class Repositories:
    def __init__(self, user: UserRepository, group: GroupRepository, nas: NasRepository):
        self.user = user
        self.group = group
        self.nas = nas


@fixture
def repositories():
    db_session = db_connect()
    try:
        yield Repositories(
            user=UserRepository(db_session),
            group=GroupRepository(db_session),
            nas=NasRepository(db_session),
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

checks = [AttributeOpValue(attribute="a", op=":=", value="b")]
replies = [AttributeOpValue(attribute="c", op=":=", value="d")]

#
# The tests.
#


def test_invalid_user():
    with raises(ValidationError):
        # Field username is required
        User()
    with raises(ValidationError):
        # User must have at least one check or one reply attribute
        #   or must have at least one group
        User(username="u")
    with raises(ValidationError):
        # Given groups have one or more duplicates
        User(
            username="u",
            checks=checks,
            replies=replies,
            groups=[UserGroup(groupname="not-unique"), UserGroup(groupname="not-unique")],
        )


def test_invalid_group():
    with raises(ValidationError):
        # Field groupname is required
        Group()
    with raises(ValidationError):
        # Group must have at least one check or one reply attribute
        #    or must have at least one user
        Group(groupname="g")
    with raises(ValidationError):
        # Given users have one or more duplicates
        Group(
            groupname="g",
            checks=checks,
            replies=replies,
            users=[GroupUser(username="not-unique"), GroupUser(username="not-unique")],
        )


def test_invalid_usergroup():
    with raises(ValidationError):
        # Field groupname is required
        UserGroup()
    with raises(ValidationError):
        # Field username is required
        GroupUser()


def test_invalid_nas():
    with raises(ValidationError):
        # Fields nasname, shortname, secret are required
        Nas()


def test_valid_user(repositories):
    u = User(username="u", checks=checks, replies=replies)

    # adding
    assert not repositories.user.exists(u.username)
    repositories.user.add(u)
    assert repositories.user.exists(u.username)

    # finding
    assert repositories.user.find_one(u.username) == u
    assert u in repositories.user.find_all()
    assert u in repositories.user.find_all(from_username="t")

    # modifying
    repositories.user.set(u.username, new_replies=checks, new_checks=replies)
    assert repositories.user.find_one(u.username).replies == checks
    assert repositories.user.find_one(u.username).checks == replies

    # removing
    repositories.user.remove(u.username)
    assert not repositories.user.exists(u.username)
    assert repositories.user.find_one(u.username) is None


def test_valid_group(repositories):
    g = Group(groupname="g", checks=checks, replies=replies)

    # adding
    assert not repositories.group.exists(g.groupname)
    repositories.group.add(g)
    assert repositories.group.exists(g.groupname)

    # finding
    assert repositories.group.find_one(g.groupname) == g
    assert g in repositories.group.find_all()
    assert g in repositories.group.find_all(from_groupname="f")

    # modifying
    repositories.group.set(g.groupname, new_replies=checks, new_checks=replies)
    assert repositories.group.find_one(g.groupname).replies == checks
    assert repositories.group.find_one(g.groupname).checks == replies

    # removing
    repositories.group.remove(g.groupname)
    assert not repositories.group.exists(g.groupname)
    assert repositories.group.find_one(g.groupname) is None


def test_valid_nas(repositories):
    n = Nas(nasname="1.1.1.1", shortname="sh", secret="se")

    # adding
    assert not repositories.nas.exists(n.nasname)
    repositories.nas.add(n)
    assert repositories.nas.exists(n.nasname)

    # finding
    assert repositories.nas.find_one(n.nasname) == n
    assert n in repositories.nas.find_all()
    assert n in repositories.nas.find_all(from_nasname="1.1.1.0")

    # modifying
    repositories.nas.set(n.nasname, new_shortname="new-sh", new_secret="new-se")
    assert repositories.nas.find_one(n.nasname).shortname == "new-sh"
    assert repositories.nas.find_one(n.nasname).secret == "new-se"

    # removing
    repositories.nas.remove(n.nasname)
    assert not repositories.nas.exists(n.nasname)
    assert repositories.nas.find_one(n.nasname) is None


def test_usergroup(repositories):
    g = Group(groupname="g", checks=checks)
    u = User(username="u", checks=checks, groups=[UserGroup(groupname=g.groupname)])

    # adding
    repositories.group.add(g)
    repositories.user.add(u)
    assert repositories.group.has_users(g.groupname)  # group has users

    # modifying
    repositories.user.set(u.username, new_groups=[])
    assert repositories.user.find_one(u.username).groups == []
    repositories.user.set(u.username, new_groups=[UserGroup(groupname=g.groupname)])
    assert repositories.user.find_one(u.username).groups == u.groups

    # removing
    repositories.user.remove(u.username)
    assert not repositories.group.has_users(g.groupname)  # group has no users
    repositories.group.remove(g.groupname)


def test_groupuser(repositories):
    u = User(username="u", checks=checks)
    g = Group(groupname="g", checks=checks, users=[GroupUser(username=u.username)])

    # adding
    repositories.user.add(u)
    repositories.group.add(g)
    assert repositories.group.has_users(g.groupname)  # group has users

    # modifying
    repositories.group.set(g.groupname, new_users=[])
    assert repositories.group.find_one(g.groupname).users == []
    repositories.group.set(g.groupname, new_users=[GroupUser(username=u.username)])
    assert repositories.group.find_one(g.groupname).users == g.users

    # removing
    repositories.user.remove(u.username)
    assert not repositories.group.has_users(g.groupname)  # group has no users
    repositories.group.remove(g.groupname)
