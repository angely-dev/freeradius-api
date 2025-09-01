from abc import ABC
from contextlib import contextmanager
from typing import List

from pydantic import BaseModel, conint, constr, model_validator

from .config import RadTables

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

    @model_validator(mode="after")
    def check_fields_on_init(self):
        checks = self.checks
        replies = self.replies
        groups = self.groups

        if not (checks or replies or groups):
            raise ValueError("User must have at least one check or one reply attribute"
                             ", or must have at least one group")

        groupnames = [group.groupname for group in groups]
        if not len(groupnames) == len(set(groupnames)):
            raise ValueError("Given groups have one or more duplicates")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "my-user",
                    "checks": [
                        AttributeOpValue(attribute="Cleartext-Password", op=":=", value="my-pass").model_dump()
                    ],
                    "replies": [
                        AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.1").model_dump(),
                        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24").model_dump(),
                        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24").model_dump(),
                        AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="my-vrf").model_dump()
                    ],
                    "groups": [UserGroup(groupname="my-group").model_dump()]
                }
            ]
        }
    }


class UserUpdate(BaseModel):
    checks: List[AttributeOpValue] = None
    replies: List[AttributeOpValue] = None
    groups: List[UserGroup] = None

    @model_validator(mode="after")
    def check_fields_on_init(self):
        checks = self.checks
        replies = self.replies
        groups = self.groups

        if checks is None and replies is None and groups is None:
            raise ValueError("Request must have at least one check, one reply attribute or one group")

        if groups:
            groupnames = [group.groupname for group in groups]
            if not len(groupnames) == len(set(groupnames)):
                raise ValueError("Given groups have one or more duplicates")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "checks": [
                        AttributeOpValue(attribute="Cleartext-Password", op=":=", value="my-pass").model_dump()
                    ]
                }
            ]
        }
    }


class Group(BaseModel):
    groupname: constr(min_length=1)
    checks: List[AttributeOpValue] = []
    replies: List[AttributeOpValue] = []

    @model_validator(mode="after")
    def check_fields_on_init(self):
        checks = self.checks
        replies = self.replies

        if not (checks or replies):
            raise ValueError("Group must have at least one check or one reply attribute")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "groupname": "my-group",
                    "checks": [
                        AttributeOpValue(attribute="Auth-Type", op=":=", value="Accept").model_dump()
                    ],
                    "replies": [
                        AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.1").model_dump(),
                        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24").model_dump()
                    ]
                }
            ]
        }
    }


class GroupUpdate(BaseModel):
    checks: List[AttributeOpValue] = None
    replies: List[AttributeOpValue] = None

    @model_validator(mode="after")
    def check_fields_on_init(self):
        checks = self.checks
        replies = self.replies

        if checks is None and replies is None:
            raise ValueError("Request must have at least one check or one reply attribute")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "replies": [
                        AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.2").model_dump()
                    ]
                }
            ]
        }
    }


class Nas(BaseModel):
    nasname: constr(min_length=1)
    shortname: str = ""
    type: str = "other"
    ports: int = 0
    secret: constr(min_length=1)
    server: str = ""
    community: str = ""
    description: str = ""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nasname": "192.168.1.10",
                    "shortname": "my-nas",
                    "type": "cisco",
                    "ports": 10,
                    "secret": "my-secret",
                    "server": "",
                    "community": "",
                    "description": "My Cisco NAS"
                }
            ]
        }
    }


class NasUpdate(BaseModel):
    shortname: str = None
    type: str = None
    ports: int = None
    secret: str = None
    server: str = None
    community: str = None
    description: str = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "secret": "new-secret"
                }
            ]
        }
    }


class BaseRepository(ABC):
    _PER_PAGE = 100

    def __init__(self, db_connection, db_tables: RadTables):
        self.db_connection = db_connection
        self.db_tables = db_tables
        # Unpack table names for easier access
        self.radcheck = db_tables.radcheck
        self.radreply = db_tables.radreply
        self.radgroupcheck = db_tables.radgroupcheck
        self.radgroupreply = db_tables.radgroupreply
        self.radusergroup = db_tables.radusergroup
        self.nas = db_tables.nas

    @contextmanager
    def _db_cursor(self):
        db_cursor = self.db_connection.cursor()
        try:
            yield db_cursor
            self.db_connection.commit()
        except Exception:
            self.db_connection.rollback()
            raise
        finally:
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
            results = db_cursor.fetchall()
            if not results:
                return False
            counts = [count for count, in results]
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
            sql = f"SELECT attribute, op, value FROM {self.radcheck} WHERE username = %s"
            db_cursor.execute(sql, (username, ))
            checks = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f"SELECT attribute, op, value FROM {self.radreply} WHERE username = %s"
            db_cursor.execute(sql, (username, ))
            replies = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f"SELECT groupname, priority FROM {self.radusergroup} WHERE username = %s"
            db_cursor.execute(sql, (username, ))
            groups = [UserGroup(groupname=g, priority=p) for g, p in db_cursor.fetchall()]

            return User(username=username, checks=checks, replies=replies, groups=groups)

    def add(self, user: User):
        with self._db_cursor() as db_cursor:
            for check in user.checks:
                sql = f"INSERT INTO {self.radcheck} (username, attribute, op, value) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(sql, (user.username, check.attribute, check.op, check.value))

            for reply in user.replies:
                sql = f"INSERT INTO {self.radreply} (username, attribute, op, value) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(sql, (user.username, reply.attribute, reply.op, reply.value))

            for group in user.groups:
                sql = f"INSERT INTO {self.radusergroup} (username, groupname, priority) VALUES (%s, %s, %s)"
                db_cursor.execute(sql, (user.username, group.groupname, group.priority))

    def update(self, username: str, user: UserUpdate):
        with self._db_cursor() as db_cursor:
            if user.checks is not None:
                db_cursor.execute(f"DELETE FROM {self.radcheck} WHERE username = %s", (username, ))
                for check in user.checks:
                    sql = f"INSERT INTO {self.radcheck} (username, attribute, op, value) VALUES (%s, %s, %s, %s)"
                    db_cursor.execute(sql, (username, check.attribute, check.op, check.value))

            if user.replies is not None:
                db_cursor.execute(f"DELETE FROM {self.radreply} WHERE username = %s", (username, ))
                for reply in user.replies:
                    sql = f"INSERT INTO {self.radreply} (username, attribute, op, value) VALUES (%s, %s, %s, %s)"
                    db_cursor.execute(sql, (username, reply.attribute, reply.op, reply.value))

            if user.groups is not None:
                db_cursor.execute(f"DELETE FROM {self.radusergroup} WHERE username = %s", (username, ))
                for group in user.groups:
                    sql = f"INSERT INTO {self.radusergroup} (username, groupname, priority) VALUES (%s, %s, %s)"
                    db_cursor.execute(sql, (username, group.groupname, group.priority))

    def delete(self, username: str):
        with self._db_cursor() as db_cursor:
            db_cursor.execute(f"DELETE FROM {self.radcheck} WHERE username = %s", (username, ))
            db_cursor.execute(f"DELETE FROM {self.radreply} WHERE username = %s", (username, ))
            db_cursor.execute(f"DELETE FROM {self.radusergroup} WHERE username = %s", (username, ))


class GroupRepository(BaseRepository):
    def __init__(self, db_connection, db_tables: RadTables):
        super().__init__(db_connection, db_tables)

    def exists(self, groupname: str) -> bool:
        with self._db_cursor() as db_cursor:
            sql = f"""SELECT COUNT(DISTINCT groupname) FROM {self.radgroupcheck} WHERE groupname = %s
                UNION SELECT COUNT(DISTINCT groupname) FROM {self.radgroupreply} WHERE groupname = %s"""
            db_cursor.execute(sql, (groupname, groupname))
            results = db_cursor.fetchall()
            if not results:
                return False
            counts = [count for count, in results]
            return sum(counts) > 0

    def find_all_groupnames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"""SELECT DISTINCT groupname FROM {self.radgroupcheck}
                UNION SELECT DISTINCT groupname FROM {self.radgroupreply}"""
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
                ) g WHERE groupname > %s ORDER BY groupname LIMIT {self._PER_PAGE}
            """
            db_cursor.execute(sql, (from_groupname, ))
            groupnames = [groupname for groupname, in db_cursor.fetchall()]
            return groupnames

    def find_one(self, groupname: str) -> Group:
        if not self.exists(groupname):
            return None

        with self._db_cursor() as db_cursor:
            sql = f"SELECT attribute, op, value FROM {self.radgroupcheck} WHERE groupname = %s"
            db_cursor.execute(sql, (groupname, ))
            checks = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f"SELECT attribute, op, value FROM {self.radgroupreply} WHERE groupname = %s"
            db_cursor.execute(sql, (groupname, ))
            replies = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            return Group(groupname=groupname, checks=checks, replies=replies)

    def add(self, group: Group):
        with self._db_cursor() as db_cursor:
            for check in group.checks:
                sql = f"INSERT INTO {self.radgroupcheck} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(sql, (group.groupname, check.attribute, check.op, check.value))

            for reply in group.replies:
                sql = f"INSERT INTO {self.radgroupreply} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(sql, (group.groupname, reply.attribute, reply.op, reply.value))

    def update(self, groupname: str, group: GroupUpdate):
        with self._db_cursor() as db_cursor:
            if group.checks is not None:
                db_cursor.execute(f"DELETE FROM {self.radgroupcheck} WHERE groupname = %s", (groupname, ))
                for check in group.checks:
                    sql = f"INSERT INTO {self.radgroupcheck} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)"
                    db_cursor.execute(sql, (groupname, check.attribute, check.op, check.value))

            if group.replies is not None:
                db_cursor.execute(f"DELETE FROM {self.radgroupreply} WHERE groupname = %s", (groupname, ))
                for reply in group.replies:
                    sql = f"INSERT INTO {self.radgroupreply} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)"
                    db_cursor.execute(sql, (groupname, reply.attribute, reply.op, reply.value))

    def delete(self, groupname: str):
        with self._db_cursor() as db_cursor:
            db_cursor.execute(f"DELETE FROM {self.radgroupcheck} WHERE groupname = %s", (groupname, ))
            db_cursor.execute(f"DELETE FROM {self.radgroupreply} WHERE groupname = %s", (groupname, ))
            db_cursor.execute(f"DELETE FROM {self.radusergroup} WHERE groupname = %s", (groupname, ))


class NasRepository(BaseRepository):
    def __init__(self, db_connection, db_tables: RadTables):
        super().__init__(db_connection, db_tables)

    def exists(self, nasname: str) -> bool:
        with self._db_cursor() as db_cursor:
            sql = f"SELECT COUNT(*) FROM {self.nas} WHERE nasname = %s"
            db_cursor.execute(sql, (nasname, ))
            result = db_cursor.fetchone()
            if result is None or len(result) == 0:
                return False
            count, = result
            return count > 0

    def find_all_nasnames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"SELECT nasname FROM {self.nas} ORDER BY nasname"
            db_cursor.execute(sql)
            nasnames = [nasname for nasname, in db_cursor.fetchall()]
            return nasnames

    def find_nasnames(self, from_nasname: str = None) -> List[str]:
        if not from_nasname:
            return self._find_first_nasnames()
        return self._find_next_nasnames(from_nasname)

    def _find_first_nasnames(self) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"SELECT nasname FROM {self.nas} ORDER BY nasname LIMIT {self._PER_PAGE}"
            db_cursor.execute(sql)
            nasnames = [nasname for nasname, in db_cursor.fetchall()]
            return nasnames

    def _find_next_nasnames(self, from_nasname: str) -> List[str]:
        with self._db_cursor() as db_cursor:
            sql = f"SELECT nasname FROM {self.nas} WHERE nasname > %s ORDER BY nasname LIMIT {self._PER_PAGE}"
            db_cursor.execute(sql, (from_nasname, ))
            nasnames = [nasname for nasname, in db_cursor.fetchall()]
            return nasnames

    def find_one(self, nasname: str) -> Nas:
        if not self.exists(nasname):
            return None

        with self._db_cursor() as db_cursor:
            sql = f"""SELECT nasname, shortname, type, ports, secret, server, community, description
                FROM {self.nas} WHERE nasname = %s"""
            db_cursor.execute(sql, (nasname, ))
            row = db_cursor.fetchone()
            if not row:
                return None

            return Nas(
                nasname=row[0],
                shortname=row[1] or "",
                type=row[2] or "other",
                ports=row[3] or 0,
                secret=row[4] or "",
                server=row[5] or "",
                community=row[6] or "",
                description=row[7] or ""
            )

    def add(self, nas: Nas):
        with self._db_cursor() as db_cursor:
            sql = f"""INSERT INTO {self.nas} (nasname, shortname, type, ports, secret, server, community, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            db_cursor.execute(sql, (
                nas.nasname,
                nas.shortname,
                nas.type,
                nas.ports,
                nas.secret,
                nas.server,
                nas.community,
                nas.description
            ))

    def update(self, nasname: str, nas: NasUpdate):
        with self._db_cursor() as db_cursor:
            # Build dynamic UPDATE query based on provided fields
            fields = []
            values = []
            if nas.shortname is not None:
                fields.append("shortname = %s")
                values.append(nas.shortname)
            if nas.type is not None:
                fields.append("type = %s")
                values.append(nas.type)
            if nas.ports is not None:
                fields.append("ports = %s")
                values.append(nas.ports)
            if nas.secret is not None:
                fields.append("secret = %s")
                values.append(nas.secret)
            if nas.server is not None:
                fields.append("server = %s")
                values.append(nas.server)
            if nas.community is not None:
                fields.append("community = %s")
                values.append(nas.community)
            if nas.description is not None:
                fields.append("description = %s")
                values.append(nas.description)

            if fields:
                sql = f"UPDATE {self.nas} SET {", ".join(fields)} WHERE nasname = %s"
                values.append(nasname)
                db_cursor.execute(sql, values)

    def delete(self, nasname: str):
        with self._db_cursor() as db_cursor:
            db_cursor.execute(f"DELETE FROM {self.nas} WHERE nasname = %s", (nasname, ))
