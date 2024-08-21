from database import db_connection, db_tables
from pydantic import ValidationError
from pyfreeradius import User, Group, Nas, AttributeOpValue, UserGroup, GroupUser
from pyfreeradius import UserRepository, GroupRepository, NasRepository
from pytest import raises

# Load the FreeRADIUS repositories
user_repo = UserRepository(db_connection, db_tables)
group_repo = GroupRepository(db_connection, db_tables)
nas_repo = NasRepository(db_connection, db_tables)

# Some dumb attributes for the tests
checks = [AttributeOpValue(attribute='a', op=':=', value='b')]
replies = [AttributeOpValue(attribute='c', op=':=', value='d')]

def test_invalid_user():
    with raises(ValidationError):
        # Field username is required
        User()
    with raises(ValidationError):
        # User must have at least one check or one reply attribute
        #   or must have at least one group
        User(username='u')
    with raises(ValidationError):
        # Given groups have one or more duplicates
        User(
            username='u',
            checks=checks,
            replies=replies,
            groups=[
                UserGroup(groupname='not-unique'),
                UserGroup(groupname='not-unique')
            ]
        )

def test_invalid_group():
    with raises(ValidationError):
        # Field groupname is required
        Group()
    with raises(ValidationError):
        # Group must have at least one check or one reply attribute
        Group(groupname='g')
    with raises(ValidationError):
        # Given users have one or more duplicates
        Group(
            groupname='g',
            checks=checks,
            replies=replies,
            users=[
                GroupUser(username='not-unique'),
                GroupUser(username='not-unique')
            ]
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
    u = User(username='u', checks=checks, replies=replies)

    # Repository: adding
    assert not user_repo.exists(u.username)
    user_repo.add(u)
    assert user_repo.exists(u.username)

    # Repository: finding
    assert user_repo.find_one(u.username) == u
    assert u.username in user_repo.find_all_usernames()
    assert u.username in user_repo.find_usernames()
    assert u.username in user_repo.find_usernames(from_username='t')

    # Repository: removing
    user_repo.remove(u.username)
    assert not user_repo.exists(u.username)
    assert user_repo.find_one(u.username) is None

def test_valid_group():
    # Model: valid instance
    g = Group(groupname='g', checks=checks, replies=replies)

    # Repository: adding
    assert not group_repo.exists(g.groupname)
    group_repo.add(g)
    assert group_repo.exists(g.groupname)

    # Repository: finding
    assert group_repo.find_one(g.groupname) == g
    assert g.groupname in group_repo.find_all_groupnames()
    assert g.groupname in group_repo.find_groupnames()
    assert g.groupname in group_repo.find_groupnames(from_groupname='f')

    # Repository: removing
    group_repo.remove(g.groupname)
    assert not group_repo.exists(g.groupname)
    assert group_repo.find_one(g.groupname) is None

def test_valid_nas():
    n = Nas(nasname='1.1.1.1', shortname='sh', secret='se')

    # Repository: adding
    assert not nas_repo.exists(n.nasname)
    nas_repo.add(n)
    assert nas_repo.exists(n.nasname)

    # Repository: finding
    assert nas_repo.find_one(n.nasname) == n
    assert str(n.nasname) in nas_repo.find_all_nasnames()
    assert str(n.nasname) in nas_repo.find_nasnames()
    assert str(n.nasname) in nas_repo.find_nasnames(from_nasname='1.1.1.0')

    # Repository: removing
    nas_repo.remove(n.nasname)
    assert not nas_repo.exists(n.nasname)
    assert nas_repo.find_one(n.nasname) is None

def test_usergroup():
    g = Group(groupname='g', checks=checks)
    u = User(username='u', groups=[UserGroup(groupname=g.groupname)])

    # Repository: adding
    group_repo.add(g)
    user_repo.add(u)
    assert group_repo.has_users(g.groupname) # group has users

    # Repository: removing
    user_repo.remove(u.username)
    assert not group_repo.has_users(g.groupname) # group has no users
    group_repo.remove(g.groupname)

def test_groupuser():
    u = User(username='u', checks=checks)
    g = Group(groupname='g', checks=checks, users=[GroupUser(username=u.username)])

    # Repository: adding
    user_repo.add(u)
    group_repo.add(g)
    assert group_repo.has_users(g.groupname) # group has users

    # Repository: removing
    user_repo.remove(u.username)
    assert not group_repo.has_users(g.groupname) # group has no users
    group_repo.remove(g.groupname)
