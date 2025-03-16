from pydantic import ValidationError
from pytest import raises

from database import db_connect
from pyfreeradius.models import AttributeOpValue, Group, GroupUser, Nas, User, UserGroup
from pyfreeradius.repositories import GroupRepository, NasRepository, UserRepository

# Load the FreeRADIUS repositories
db_connection = db_connect()
user_repo = UserRepository(db_connection)
group_repo = GroupRepository(db_connection)
nas_repo = NasRepository(db_connection)

# Some dumb attributes for the tests
checks = [AttributeOpValue(attribute="a", op=":=", value="b")]
replies = [AttributeOpValue(attribute="c", op=":=", value="d")]


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


def test_valid_user():
    u = User(username="u", checks=checks, replies=replies)

    # adding
    assert not user_repo.exists(u.username)
    user_repo.add(u)
    assert user_repo.exists(u.username)

    # finding
    assert user_repo.find_one(u.username) == u
    assert u in user_repo.find_all()
    assert u in user_repo.find_all(from_username="t")

    # modifying
    user_repo.set(u.username, new_replies=checks, new_checks=replies)
    assert user_repo.find_one(u.username).replies == checks
    assert user_repo.find_one(u.username).checks == replies

    # removing
    user_repo.remove(u.username)
    assert not user_repo.exists(u.username)
    assert user_repo.find_one(u.username) is None


def test_valid_group():
    g = Group(groupname="g", checks=checks, replies=replies)

    # adding
    assert not group_repo.exists(g.groupname)
    group_repo.add(g)
    assert group_repo.exists(g.groupname)

    # finding
    assert group_repo.find_one(g.groupname) == g
    assert g in group_repo.find_all()
    assert g in group_repo.find_all(from_groupname="f")

    # modifying
    group_repo.set(g.groupname, new_replies=checks, new_checks=replies)
    assert group_repo.find_one(g.groupname).replies == checks
    assert group_repo.find_one(g.groupname).checks == replies

    # removing
    group_repo.remove(g.groupname)
    assert not group_repo.exists(g.groupname)
    assert group_repo.find_one(g.groupname) is None


def test_valid_nas():
    n = Nas(nasname="1.1.1.1", shortname="sh", secret="se")

    # adding
    assert not nas_repo.exists(n.nasname)
    nas_repo.add(n)
    assert nas_repo.exists(n.nasname)

    # finding
    assert nas_repo.find_one(n.nasname) == n
    assert n in nas_repo.find_all()
    assert n in nas_repo.find_all(from_nasname="1.1.1.0")

    # modifying
    nas_repo.set(n.nasname, new_shortname="new-sh", new_secret="new-se")
    assert nas_repo.find_one(n.nasname).shortname == "new-sh"
    assert nas_repo.find_one(n.nasname).secret == "new-se"

    # removing
    nas_repo.remove(n.nasname)
    assert not nas_repo.exists(n.nasname)
    assert nas_repo.find_one(n.nasname) is None


def test_usergroup():
    g = Group(groupname="g", checks=checks)
    u = User(username="u", checks=checks, groups=[UserGroup(groupname=g.groupname)])

    # adding
    group_repo.add(g)
    user_repo.add(u)
    assert group_repo.has_users(g.groupname)  # group has users

    # modifying
    user_repo.set(u.username, new_groups=[])
    assert user_repo.find_one(u.username).groups == []
    user_repo.set(u.username, new_groups=[UserGroup(groupname=g.groupname)])
    assert user_repo.find_one(u.username).groups == u.groups

    # removing
    user_repo.remove(u.username)
    assert not group_repo.has_users(g.groupname)  # group has no users
    group_repo.remove(g.groupname)


def test_groupuser():
    u = User(username="u", checks=checks)
    g = Group(groupname="g", checks=checks, users=[GroupUser(username=u.username)])

    # adding
    user_repo.add(u)
    group_repo.add(g)
    assert group_repo.has_users(g.groupname)  # group has users

    # modifying
    group_repo.set(g.groupname, new_users=[])
    assert group_repo.find_one(g.groupname).users == []
    group_repo.set(g.groupname, new_users=[GroupUser(username=u.username)])
    assert group_repo.find_one(g.groupname).users == g.users

    # removing
    user_repo.remove(u.username)
    assert not group_repo.has_users(g.groupname)  # group has no users
    group_repo.remove(g.groupname)
