from abc import ABC, abstractmethod
from contextlib import contextmanager
from pydantic import BaseModel, IPvAnyAddress, constr, conint, root_validator
from typing import List

#
# The Pydantic models implement the UML class diagram;
# it is NOT a one-to-one mapping with database tables.
#
# The association between User and Group is implemented
# with two models (one for each direction).
#

class AttributeOpValue(BaseModel):
    attribute: constr(min_length=1)
    op: constr(min_length=1)
    value: constr(min_length=1)

class UserGroup(BaseModel):
    groupname: constr(min_length=1)
    priority: conint(ge=1) = 1

class GroupUser(BaseModel):
    username: constr(min_length=1)
    priority: conint(ge=1) = 1

class User(BaseModel):
    username: constr(min_length=1)
    checks: List[AttributeOpValue] = []
    replies: List[AttributeOpValue] = []
    groups: List[UserGroup] = []

    @root_validator
    def check_fields_on_init(cls, values):
        checks = values.get('checks')
        replies = values.get('replies')
        groups = values.get('groups')

        if not (checks or replies or groups):
            raise ValueError('User must have at least one check or one reply attribute'
                             ', or must have at least one group')

        groupnames = [group.groupname for group in groups]
        if not len(groupnames) == len(set(groupnames)):
            raise ValueError('Given groups have one or more duplicates')

        return values

    class Config:
        schema_extra = {
            'examples': [
                {
                'username': 'my-user',
                    'checks': [
                        AttributeOpValue(attribute='Cleartext-Password', op=':=', value='my-pass')
                    ],
                    'replies': [
                        AttributeOpValue(attribute='Framed-IP-Address', op=':=', value='10.0.0.1'),
                        AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.1.0/24'),
                        AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.2.0/24'),
                        AttributeOpValue(attribute='Huawei-Vpn-Instance', op=':=', value='my-vrf')
                    ],
                    'groups': [UserGroup(groupname='my-group')]
                }
            ]
        }

class Group(BaseModel):
    groupname: constr(min_length=1)
    checks: List[AttributeOpValue] = []
    replies: List[AttributeOpValue] = []
    users: List[GroupUser] = []

    @root_validator
    def check_fields_on_init(cls, values):
        checks = values.get('checks')
        replies = values.get('replies')
        users = values.get('users')

        if not (checks or replies):
            raise ValueError('Group must have at least one check or one reply attribute')

        usernames = [user.username for user in users]
        if not len(usernames) == len(set(usernames)):
            raise ValueError('Given users have one or more duplicates')

        return values

    class Config:
        schema_extra = {
            'examples': [
                {
                    'groupname': 'my-group',
                    'replies': [AttributeOpValue(attribute='Filter-Id', op=':=', value='10m')]
                }
            ]
        }

class Nas(BaseModel):
    nasname: IPvAnyAddress
    shortname: constr(min_length=1)
    secret: constr(min_length=1)

    class Config:
        schema_extra = {
            'examples': [
                {
                    'nasname': '5.5.5.5',
                    'shortname': 'my-nas',
                    'secret': 'my-secret'
                }
            ]
        }

#
# As per the Repository pattern, repositories implement the mapping
# between the Domain Objects (the Pydantic models) and the database.
# The BaseRepository is the abstract superclass of the repositories.
#

class RadTables(BaseModel):
    radcheck: str = 'radcheck'
    radreply: str = 'radreply'
    radgroupcheck: str = 'radgroupcheck'
    radgroupreply: str = 'radgroupreply'
    radusergroup: str = 'radusergroup'
    nas: str = 'nas'

class BaseRepository(ABC):
    # Number of items per page
    _PER_PAGE = 20

    # The constructor sets the DB context (connection and table names)
    @abstractmethod
    def __init__(self, db_connection, db_tables: RadTables):
        self.db_connection = db_connection
        self.radcheck = db_tables.radcheck
        self.radreply = db_tables.radreply
        self.radgroupcheck = db_tables.radgroupcheck
        self.radgroupreply = db_tables.radgroupreply
        self.radusergroup = db_tables.radusergroup
        self.nas = db_tables.nas

    # This contextmanager properly opens/closes the DB cursor and transaction
    # (some drivers not supporting this feature yet with autocommit enabled)
    @contextmanager
    def _db_cursor(self):
        db_cursor = self.db_connection.cursor()
        try:
            yield db_cursor
        finally:
            self.db_connection.commit()
            db_cursor.close()

class UserRepository(BaseRepository):
    def __init__(self, db_connection, db_tables: RadTables):
        super().__init__(db_connection, db_tables)

    def exists(self, username: str) -> bool:
        with self._db_cursor() as db_cursor:
            sql = f"""SELECT COUNT(DISTINCT username) FROM {self.radcheck} WHERE username = %s
                UNION SELECT COUNT(DISTINCT username) FROM {self.radreply} WHERE username = %s
                UNION SELECT COUNT(DISTINCT username) FROM {self.radusergroup} WHERE username = %s"""
            db_cursor.execute(sql, (username, username, username))
            counts = [count for count, in db_cursor.fetchall()]
            return sum(counts) > 0

    def find_all_usernames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""SELECT DISTINCT username FROM {self.radcheck}
                UNION SELECT DISTINCT username FROM {self.radreply}
                UNION SELECT DISTINCT username FROM {self.radusergroup}"""
            db_cursor.execute(sql)
            usernames = [username for username, in db_cursor.fetchall()]
            return usernames

    def find_usernames(self, from_username: str = None) -> List[str]:
        if not from_username:
            return self._find_first_usernames()
        return self._find_next_usernames(from_username)

    def _find_first_usernames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""
                SELECT username FROM (
                        SELECT DISTINCT username FROM {self.radcheck}
                  UNION SELECT DISTINCT username FROM {self.radreply}
                  UNION SELECT DISTINCT username FROM {self.radusergroup}
                ) u ORDER BY username LIMIT {self._PER_PAGE}
            """
            db_cursor.execute(sql)
            usernames = [username for username, in db_cursor.fetchall()]
            return usernames

    def _find_next_usernames(self, from_username: str) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""
                SELECT username FROM (
                        SELECT DISTINCT username FROM {self.radcheck}
                  UNION SELECT DISTINCT username FROM {self.radreply}
                  UNION SELECT DISTINCT username FROM {self.radusergroup}
                ) u WHERE username > %s ORDER BY username LIMIT {self._PER_PAGE}
            """
            db_cursor.execute(sql, (from_username, ))
            usernames = [username for username, in db_cursor.fetchall()]
            return usernames

    def find_one(self, username: str) -> User:
        if not self.exists(username):
            return None

        with self._db_cursor() as db_cursor:
            sql = f'SELECT attribute, op, value FROM {self.radcheck} WHERE username = %s'
            db_cursor.execute(sql, (username, ))
            checks = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f'SELECT attribute, op, value FROM {self.radreply} WHERE username = %s'
            db_cursor.execute(sql, (username, ))
            replies = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f'SELECT groupname, priority FROM {self.radusergroup} WHERE username = %s'
            db_cursor.execute(sql, (username, ))
            groups = [UserGroup(groupname=g, priority=p) for g, p in db_cursor.fetchall()]

            return User(username=username, checks=checks, replies=replies, groups=groups)

    def add(self, user: User):
        with self._db_cursor() as db_cursor:
            for check in user.checks:
                sql = f'INSERT INTO {self.radcheck} (username, attribute, op, value) VALUES (%s, %s, %s, %s)'
                db_cursor.execute(sql, (user.username, check.attribute, check.op, check.value))

            for reply in user.replies:
                sql = f'INSERT INTO {self.radreply} (username, attribute, op, value) VALUES (%s, %s, %s, %s)'
                db_cursor.execute(sql, (user.username, reply.attribute, reply.op, reply.value))

            for group in user.groups:
                sql = f'INSERT INTO {self.radusergroup} (username, groupname, priority) VALUES (%s, %s, %s)'
                db_cursor.execute(sql, (user.username, group.groupname, group.priority))

    def remove(self, username: str):
        with self._db_cursor() as db_cursor:
            db_cursor.execute(f'DELETE FROM {self.radcheck} WHERE username = %s', (username, ))
            db_cursor.execute(f'DELETE FROM {self.radreply} WHERE username = %s', (username, ))
            db_cursor.execute(f'DELETE FROM {self.radusergroup} WHERE username = %s', (username, ))

class GroupRepository(BaseRepository):
    def __init__(self, db_connection, db_tables: RadTables):
        super().__init__(db_connection, db_tables)

    def exists(self, groupname: str) -> bool:
        with self._db_cursor() as db_cursor:
            sql = f"""SELECT COUNT(DISTINCT groupname) FROM {self.radgroupcheck} WHERE groupname = %s
                UNION SELECT COUNT(DISTINCT groupname) FROM {self.radgroupreply} WHERE groupname = %s
                UNION SELECT COUNT(DISTINCT groupname) FROM {self.radusergroup} WHERE groupname = %s"""
            db_cursor.execute(sql, (groupname, groupname, groupname))
            counts = [count for count, in db_cursor.fetchall()]
            return sum(counts) > 0

    def find_all_groupnames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""SELECT DISTINCT groupname FROM {self.radgroupcheck}
                UNION SELECT DISTINCT groupname FROM {self.radgroupreply}
                UNION SELECT DISTINCT groupname FROM {self.radusergroup}"""
            db_cursor.execute(sql)
            groupnames = [groupname for groupname, in db_cursor.fetchall()]
            return groupnames

    def find_groupnames(self, from_groupname: str = None) -> List[str]:
        if not from_groupname:
            return self._find_first_groupnames()
        return self._find_next_groupnames(from_groupname)

    def _find_first_groupnames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""
                SELECT groupname FROM (
                        SELECT DISTINCT groupname FROM {self.radgroupcheck}
                  UNION SELECT DISTINCT groupname FROM {self.radgroupreply}
                  UNION SELECT DISTINCT groupname FROM {self.radusergroup}
                ) g ORDER BY groupname LIMIT {self._PER_PAGE}
            """
            db_cursor.execute(sql)
            groupnames = [groupname for groupname, in db_cursor.fetchall()]
            return groupnames

    def _find_next_groupnames(self, from_groupname: str) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""
                SELECT groupname FROM (
                        SELECT DISTINCT groupname FROM {self.radgroupcheck}
                  UNION SELECT DISTINCT groupname FROM {self.radgroupreply}
                  UNION SELECT DISTINCT groupname FROM {self.radusergroup}
                ) g WHERE groupname > %s ORDER BY groupname LIMIT {self._PER_PAGE}
            """
            db_cursor.execute(sql, (from_groupname, ))
            groupnames = [groupname for groupname, in db_cursor.fetchall()]
            return groupnames

    def has_users(self, groupname: str) -> bool:
        with self._db_cursor() as db_cursor:
            sql = f'SELECT COUNT(DISTINCT username) FROM {self.radusergroup} WHERE groupname = %s'
            db_cursor.execute(sql,(groupname, ))
            count, = db_cursor.fetchone()
            return count > 0

    def find_one(self, groupname: str) -> Group:
        if not self.exists(groupname):
            return None

        with self._db_cursor() as db_cursor:
            sql = f'SELECT attribute, op, value FROM {self.radgroupcheck} WHERE groupname = %s'
            db_cursor.execute(sql, (groupname, ))
            checks = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f'SELECT attribute, op, value FROM {self.radgroupreply} WHERE groupname = %s'
            db_cursor.execute(sql, (groupname, ))
            replies = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f'SELECT username, priority FROM {self.radusergroup} WHERE groupname = %s'
            db_cursor.execute(sql, (groupname, ))
            users = [GroupUser(username=u, priority=p) for u, p in db_cursor.fetchall()]

            return Group(groupname=groupname, checks=checks, replies=replies, users=users)

    def add(self, group: Group):
        with self._db_cursor() as db_cursor:
            for check in group.checks:
                sql = f'INSERT INTO {self.radgroupcheck} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)'
                db_cursor.execute(sql, (group.groupname, check.attribute, check.op, check.value))

            for reply in group.replies:
                sql = f'INSERT INTO {self.radgroupreply} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)'
                db_cursor.execute(sql, (group.groupname, reply.attribute, reply.op, reply.value))

            for user in group.users:
                sql = f'INSERT INTO {self.radusergroup} (groupname, username, priority) VALUES (%s, %s, %s)'
                db_cursor.execute(sql, (group.groupname, user.username, user.priority))

    def remove(self, groupname: str) -> bool:
        with self._db_cursor() as db_cursor:
            db_cursor.execute(f'DELETE FROM {self.radgroupcheck} WHERE groupname = %s', (groupname, ))
            db_cursor.execute(f'DELETE FROM {self.radgroupreply} WHERE groupname = %s', (groupname, ))
            db_cursor.execute(f'DELETE FROM {self.radusergroup} WHERE groupname = %s', (groupname, ))

class NasRepository(BaseRepository):
    def __init__(self, db_connection, db_tables: RadTables):
        super().__init__(db_connection, db_tables)

    def exists(self, nasname: IPvAnyAddress) -> bool:
        with self._db_cursor() as db_cursor:
            sql = f'SELECT COUNT(DISTINCT nasname) FROM {self.nas} WHERE nasname = %s'
            db_cursor.execute(sql, (str(nasname), ))
            count, = db_cursor.fetchone()
            return count > 0

    def find_all_nasnames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f'SELECT DISTINCT nasname FROM {self.nas}'
            db_cursor.execute(sql)
            nasnames = [nasname for nasname, in db_cursor.fetchall()]
            return nasnames

    def find_nasnames(self, from_nasname: IPvAnyAddress = None) -> List[str]:
        if not from_nasname:
            return self._find_first_nasnames()
        return self._find_next_nasnames(from_nasname)

    def _find_first_nasnames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""SELECT DISTINCT nasname FROM {self.nas}
                      ORDER BY nasname LIMIT {self._PER_PAGE}"""
            db_cursor.execute(sql)
            nasnames = [nasname for nasname, in db_cursor.fetchall()]
            return nasnames

    def _find_next_nasnames(self, from_nasname: IPvAnyAddress) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""SELECT DISTINCT nasname FROM {self.nas}
                      WHERE nasname > %s ORDER BY nasname LIMIT {self._PER_PAGE}"""
            db_cursor.execute(sql, (str(from_nasname), ))
            nasnames = [nasname for nasname, in db_cursor.fetchall()]
            return nasnames

    def find_one(self, nasname: IPvAnyAddress) -> Nas:
        if not self.exists(nasname):
            return None

        with self._db_cursor() as db_cursor:
            sql = f'SELECT nasname, shortname, secret FROM {self.nas} WHERE nasname = %s'
            db_cursor.execute(sql, (str(nasname), ))
            n, sh, se = db_cursor.fetchone()
            return Nas(nasname=n, shortname=sh, secret=se)

    def add(self, nas: Nas):
        with self._db_cursor() as db_cursor:
            sql = f'INSERT INTO {self.nas} (nasname, shortname, secret) VALUES (%s, %s, %s)'
            db_cursor.execute(sql, (str(nas.nasname), nas.shortname, nas.secret))
            self.db_connection.commit()

    def remove(self, nasname: IPvAnyAddress):
        with self._db_cursor() as db_cursor:
            db_cursor.execute(f'DELETE FROM {self.nas} WHERE nasname = %s', (str(nasname), ))
