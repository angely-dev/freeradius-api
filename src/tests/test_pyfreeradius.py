from database import db_connection, db_tables
from pydantic import ValidationError
from pyfreeradius import User, Group, Nas, AttributeOpValue, UserGroup, GroupUser
from pyfreeradius import UserRepository, GroupRepository, NasRepository
import unittest

# Load the FreeRADIUS repositories
user_repo = UserRepository(db_connection, db_tables)
group_repo = GroupRepository(db_connection, db_tables)
nas_repo = NasRepository(db_connection, db_tables)

# Some dumb attributes for the tests
checks = [AttributeOpValue(attribute='a', op=':=', value='b')]
replies = [AttributeOpValue(attribute='c', op=':=', value='d')]

class TestModelsAndRepositories(unittest.TestCase):
    def test_user(self):
        # Model: invalid instance
        self.assertRaises(ValidationError, User)               # no params
        self.assertRaises(ValidationError, User, username='u') # missing params
        self.assertRaises(ValidationError, User, username='u',
                                                 checks=checks, replies=replies,
                                                 # groupnames not unique
                                                 groups=[UserGroup(groupname='not-unique'),
                                                         UserGroup(groupname='not-unique')])

        # Model: valid instance
        u = User(username='u', checks=checks, replies=replies)

        # Repository: adding
        self.assertFalse(user_repo.exists(u.username))
        user_repo.add(u)
        self.assertTrue(user_repo.exists(u.username))

        # Repository: finding
        self.assertEqual(user_repo.find_one(u.username), u)
        self.assertIn(u.username, user_repo.find_all_usernames())
        self.assertIn(u.username, user_repo.find_usernames())
        self.assertIn(u.username, user_repo.find_usernames(from_username='t'))

        # Repository: removing
        user_repo.remove(u.username)
        self.assertFalse(user_repo.exists(u.username))
        self.assertIsNone(user_repo.find_one(u.username))

    def test_group(self):
        # Model: invalid instance
        self.assertRaises(ValidationError, Group)                # no params
        self.assertRaises(ValidationError, Group, groupname='g') # missing params
        self.assertRaises(ValidationError, Group, groupname='g',
                                                  checks=checks, replies=replies,
                                                  # usernames not unique
                                                  users=[GroupUser(username='not-unique'),
                                                         GroupUser(username='not-unique')])

        # Model: valid instance
        g = Group(groupname='g', checks=checks, replies=replies)

        # Repository: adding
        self.assertFalse(group_repo.exists(g.groupname))
        group_repo.add(g)
        self.assertTrue(group_repo.exists(g.groupname))

        # Repository: finding
        self.assertEqual(group_repo.find_one(g.groupname), g)
        self.assertIn(g.groupname, group_repo.find_all_groupnames())
        self.assertIn(g.groupname, group_repo.find_groupnames())
        self.assertIn(g.groupname, group_repo.find_groupnames(from_groupname='f'))

        # Repository: removing
        group_repo.remove(g.groupname)
        self.assertFalse(group_repo.exists(g.groupname))
        self.assertIsNone(group_repo.find_one(g.groupname))

    def test_nas(self):
        # Model: invalid instance
        self.assertRaises(ValidationError, Nas) # no params

        # Model: valid instance
        n = Nas(nasname='1.1.1.1', shortname='sh', secret='se')

        # Repository: adding
        self.assertFalse(nas_repo.exists(n.nasname))
        nas_repo.add(n)
        self.assertTrue(nas_repo.exists(n.nasname))

        # Repository: finding
        self.assertEqual(nas_repo.find_one(n.nasname), n)
        self.assertIn(str(n.nasname), nas_repo.find_all_nasnames())
        self.assertIn(str(n.nasname), nas_repo.find_nasnames())
        self.assertIn(str(n.nasname), nas_repo.find_nasnames(from_nasname='1.1.1.0'))

        # Repository: removing
        nas_repo.remove(n.nasname)
        self.assertFalse(nas_repo.exists(n.nasname))
        self.assertIsNone(nas_repo.find_one(n.nasname))

    def test_usergroup(self):
        # Model: invalid instance
        self.assertRaises(ValidationError, UserGroup) # no params

        # Model: valid instance
        ug = UserGroup(groupname='g')
        u = User(username='u', groups=[ug])
        g = Group(groupname='g', checks=checks)

        # Repository: adding
        group_repo.add(g)
        user_repo.add(u)
        self.assertTrue(group_repo.has_users(g.groupname)) # group has users

        # Repository: removing
        user_repo.remove(u.username)
        self.assertFalse(group_repo.has_users(g.groupname)) # group has no users
        group_repo.remove(g.groupname)

    def test_groupuser(self):
        # Model: invalid instance
        self.assertRaises(ValidationError, GroupUser) # no params

        # Model: valid instance
        gu = GroupUser(username='u')
        g = Group(groupname='g', checks=checks, users=[gu])
        u = User(username='u', checks=checks)

        # Repository: adding
        user_repo.add(u)
        group_repo.add(g)
        self.assertTrue(group_repo.has_users(g.groupname)) # group has users

        # Repository: removing
        user_repo.remove(u.username)
        self.assertFalse(group_repo.has_users(g.groupname)) # group has no users
        group_repo.remove(g.groupname)
