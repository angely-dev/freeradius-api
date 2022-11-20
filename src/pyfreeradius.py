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
            raise ValueError('User must have at least one check or one reply attribute, '
                             'or must belong to at least one group')

        groupnames = [group.groupname for group in groups]
        if not len(groupnames) == len(set(groupnames)):
            raise ValueError('Given groups have one or more duplicates')

        return values

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

class Nas(BaseModel):
    nasname: IPvAnyAddress
    shortname: constr(min_length=1)
    secret: constr(min_length=1)

#
# As per the Repository pattern, repositories implement the mapping
# between the Domain Objects (the Pydantic models) and the database.
#
# The BaseRepository is the (abstract) superclass of the repositories.
# The constructor sets the DB context, i.e., connection and table names.
#

class RadTables(BaseModel):
    radcheck: str = 'radcheck'
    radreply: str = 'radreply'
    radgroupcheck: str = 'radgroupcheck'
    radgroupreply: str = 'radgroupreply'
    radusergroup: str = 'radusergroup'
    nas: str = 'nas'

class BaseRepository:
    def __init__(self, db_connection, db_tables: RadTables):
        self.db_connection = db_connection
        self.radcheck = db_tables.radcheck
        self.radreply = db_tables.radreply
        self.radgroupcheck = db_tables.radgroupcheck
        self.radgroupreply = db_tables.radgroupreply
        self.radusergroup = db_tables.radusergroup
        self.nas = db_tables.nas

class UserRepository(BaseRepository):
    def exists(self, username: str) -> bool:
        sql = f"""SELECT COUNT(DISTINCT username) FROM {self.radcheck} WHERE username = %s
            UNION SELECT COUNT(DISTINCT username) FROM {self.radreply} WHERE username = %s
            UNION SELECT COUNT(DISTINCT username) FROM {self.radusergroup} where username = %s"""
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql, (username, username, username))
        counts = [count for count, in db_cursor.fetchall()]
        db_cursor.close()
        return sum(counts) > 0

    def find_all_usernames(self) -> List[str]:
        sql = f"""SELECT DISTINCT username FROM {self.radcheck}
            UNION SELECT DISTINCT username FROM {self.radreply}
            UNION SELECT DISTINCT username FROM {self.radusergroup}"""
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql)
        usernames = [username for username, in db_cursor.fetchall()]
        db_cursor.close()
        return usernames

    def find_one(self, username: str) -> User:
        if not self.exists(username):
            return None

        db_cursor = self.db_connection.cursor()

        sql = f'SELECT attribute, op, value FROM {self.radcheck} where username = %s'
        db_cursor.execute(sql, (username, ))
        checks = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

        sql = f'SELECT attribute, op, value FROM {self.radreply} where username = %s'
        db_cursor.execute(sql, (username, ))
        replies = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

        sql = f'SELECT groupname, priority FROM {self.radusergroup} where username = %s'
        db_cursor.execute(sql, (username, ))
        groups = [UserGroup(groupname=g, priority=p) for g, p in db_cursor.fetchall()]

        db_cursor.close()

        return User(username=username, checks=checks, replies=replies, groups=groups)

    def add(self, user: User):
        db_cursor = self.db_connection.cursor()

        for check in user.checks:
            sql = f'INSERT INTO {self.radcheck} (username, attribute, op, value) VALUES (%s, %s, %s, %s)'
            db_cursor.execute(sql, (user.username, check.attribute, check.op, check.value))

        for reply in user.replies:
            sql = f'INSERT INTO {self.radreply} (username, attribute, op, value) VALUES (%s, %s, %s, %s)'
            db_cursor.execute(sql, (user.username, reply.attribute, reply.op, reply.value))

        for group in user.groups:
            sql = f'INSERT INTO {self.radusergroup} (username, groupname, priority) VALUES (%s, %s, %s)'
            db_cursor.execute(sql, (user.username, group.groupname, group.priority))

        self.db_connection.commit()
        db_cursor.close()

    def remove(self, username: str):
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(f'DELETE FROM {self.radcheck} WHERE username = %s', (username, ))
        db_cursor.execute(f'DELETE FROM {self.radreply} WHERE username = %s', (username, ))
        db_cursor.execute(f'DELETE FROM {self.radusergroup} WHERE username = %s', (username, ))
        self.db_connection.commit()
        db_cursor.close()

class GroupRepository(BaseRepository):
    def exists(self, groupname: str) -> bool:
        sql = f"""SELECT COUNT(DISTINCT groupname) FROM {self.radgroupcheck} WHERE groupname = %s
            UNION SELECT COUNT(DISTINCT groupname) FROM {self.radgroupreply} WHERE groupname = %s
            UNION SELECT COUNT(DISTINCT groupname) FROM {self.radusergroup} WHERE groupname = %s"""
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql, (groupname, groupname, groupname))
        counts = [count for count, in db_cursor.fetchall()]
        db_cursor.close()
        return sum(counts) > 0

    def find_all_groupnames(self) -> List[str]:
        sql = f"""SELECT DISTINCT groupname FROM {self.radgroupcheck}
            UNION SELECT DISTINCT groupname FROM {self.radgroupreply}
            UNION SELECT DISTINCT groupname FROM {self.radusergroup}"""
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql)
        groupnames = [groupname for groupname, in db_cursor.fetchall()]
        db_cursor.close()
        return groupnames

    def has_users(self, groupname: str) -> bool:
        sql = f'SELECT COUNT(DISTINCT username) FROM {self.radusergroup} WHERE groupname = %s'
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql,(groupname, ))
        count, = db_cursor.fetchone()
        db_cursor.close()
        return count > 0

    def find_one(self, groupname: str) -> Group:
        if not self.exists(groupname):
            return None

        db_cursor = self.db_connection.cursor()

        sql = f'SELECT attribute, op, value FROM {self.radgroupcheck} where groupname = %s'
        db_cursor.execute(sql, (groupname, ))
        checks = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

        sql = f'SELECT attribute, op, value FROM {self.radgroupreply} where groupname = %s'
        db_cursor.execute(sql, (groupname, ))
        replies = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

        sql = f'SELECT username, priority FROM {self.radusergroup} where groupname = %s'
        db_cursor.execute(sql, (groupname, ))
        users = [GroupUser(username=u, priority=p) for u, p in db_cursor.fetchall()]

        db_cursor.close()

        return Group(groupname=groupname, checks=checks, replies=replies, users=users)

    def add(self, group: Group):
        db_cursor = self.db_connection.cursor()

        for check in group.checks:
            sql = f'INSERT INTO {self.radgroupcheck} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)'
            db_cursor.execute(sql, (group.groupname, check.attribute, check.op, check.value))

        for reply in group.replies:
            sql = f'INSERT INTO {self.radgroupreply} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)'
            db_cursor.execute(sql, (group.groupname, reply.attribute, reply.op, reply.value))

        for user in group.users:
            sql = f'INSERT INTO {self.radusergroup} (groupname, username, priority) VALUES (%s, %s, %s)'
            db_cursor.execute(sql, (group.groupname, user.username, user.priority))

        self.db_connection.commit()
        db_cursor.close()

    def remove(self, groupname: str) -> bool:
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(f'DELETE FROM {self.radgroupcheck} WHERE groupname = %s', (groupname, ))
        db_cursor.execute(f'DELETE FROM {self.radgroupreply} WHERE groupname = %s', (groupname, ))
        db_cursor.execute(f'DELETE FROM {self.radusergroup} WHERE groupname = %s', (groupname, ))
        self.db_connection.commit()
        db_cursor.close()

class NasRepository(BaseRepository):
    def exists(self, nasname: IPvAnyAddress) -> bool:
        sql = f'SELECT COUNT(DISTINCT nasname) FROM {self.nas} where nasname = %s'
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql, (str(nasname), ))
        count, = db_cursor.fetchone()
        db_cursor.close()
        return count > 0

    def find_all_nasnames(self) -> List[str]:
        sql = f'SELECT DISTINCT nasname FROM {self.nas}'
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql)
        nasnames = [nasname for nasname, in db_cursor.fetchall()]
        db_cursor.close()
        return nasnames

    def find_one(self, nasname: IPvAnyAddress) -> Nas:
        if not self.exists(nasname):
            return None

        sql = f'SELECT nasname, shortname, secret FROM {self.nas} WHERE nasname = %s'
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql, (str(nasname), ))
        n, sh, se = db_cursor.fetchone()
        db_cursor.close()
        return Nas(nasname=n, shortname=sh, secret=se)

    def add(self, nas: Nas):
        sql = f'INSERT INTO {self.nas} (nasname, shortname, secret) VALUES (%s, %s, %s)'
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(sql, (str(nas.nasname), nas.shortname, nas.secret))
        self.db_connection.commit()
        db_cursor.close()

    def remove(self, nasname: IPvAnyAddress):
        db_cursor = self.db_connection.cursor()
        db_cursor.execute(f'DELETE FROM {self.nas} WHERE nasname = %s', (str(nasname), ))
        self.db_connection.commit()
        db_cursor.close()
