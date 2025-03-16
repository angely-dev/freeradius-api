from abc import ABC, abstractmethod
from contextlib import closing

from settings import (
    NAS,
    PER_PAGE,
    RADCHECK,
    RADGROUPCHECK,
    RADGROUPREPLY,
    RADREPLY,
    RADUSERGROUP,
)

from .models import AttributeOpValue, Group, GroupUser, Nas, User, UserGroup

#
# As per the Repository pattern, repositories implement the mapping
# between the Domain Objects (the Pydantic models) and the database.
# The BaseRepository is the abstract superclass of the repositories.
#


class BaseRepository(ABC):
    # The constructor sets the DB context (connection and table names)
    @abstractmethod
    def __init__(self, db_connection):
        self.db_connection = db_connection


class UserRepository(BaseRepository):
    def __init__(self, db_connection):
        super().__init__(db_connection)

    def exists(self, username: str) -> bool:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""SELECT COUNT(DISTINCT username) FROM {RADCHECK} WHERE username = %s
                UNION SELECT COUNT(DISTINCT username) FROM {RADREPLY} WHERE username = %s
                UNION SELECT COUNT(DISTINCT username) FROM {RADUSERGROUP} WHERE username = %s"""
            db_cursor.execute(sql, (username, username, username))
            counts = [count for (count,) in db_cursor.fetchall()]
            return sum(counts) > 0

    def find_all_usernames(self) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""SELECT DISTINCT username FROM {RADCHECK}
                UNION SELECT DISTINCT username FROM {RADREPLY}
                UNION SELECT DISTINCT username FROM {RADUSERGROUP}"""
            db_cursor.execute(sql)
            usernames = [username for (username,) in db_cursor.fetchall()]
            return usernames

    def find_usernames(self, from_username: str | None = None) -> list[str]:
        if not from_username:
            return self._find_first_usernames()
        return self._find_next_usernames(from_username)

    def _find_first_usernames(self) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""
                SELECT username FROM (
                        SELECT DISTINCT username FROM {RADCHECK}
                  UNION SELECT DISTINCT username FROM {RADREPLY}
                  UNION SELECT DISTINCT username FROM {RADUSERGROUP}
                ) u ORDER BY username LIMIT {PER_PAGE}
            """
            db_cursor.execute(sql)
            usernames = [username for (username,) in db_cursor.fetchall()]
            return usernames

    def _find_next_usernames(self, from_username: str) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""
                SELECT username FROM (
                        SELECT DISTINCT username FROM {RADCHECK}
                  UNION SELECT DISTINCT username FROM {RADREPLY}
                  UNION SELECT DISTINCT username FROM {RADUSERGROUP}
                ) u WHERE username > %s ORDER BY username LIMIT {PER_PAGE}
            """
            db_cursor.execute(sql, (from_username,))
            usernames = [username for (username,) in db_cursor.fetchall()]
            return usernames

    def find_one(self, username: str) -> User | None:
        if not self.exists(username):
            return None

        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"SELECT attribute, op, value FROM {RADCHECK} WHERE username = %s"
            db_cursor.execute(sql, (username,))
            checks = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f"SELECT attribute, op, value FROM {RADREPLY} WHERE username = %s"
            db_cursor.execute(sql, (username,))
            replies = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f"SELECT groupname, priority FROM {RADUSERGROUP} WHERE username = %s"
            db_cursor.execute(sql, (username,))
            groups = [UserGroup(groupname=g, priority=p) for g, p in db_cursor.fetchall()]

            return User(username=username, checks=checks, replies=replies, groups=groups)

    def add(self, user: User):
        with closing(self.db_connection.cursor()) as db_cursor:
            for check in user.checks:
                sql = f"INSERT INTO {RADCHECK} (username, attribute, op, value) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(sql, (user.username, check.attribute, check.op, check.value))

            for reply in user.replies:
                sql = f"INSERT INTO {RADREPLY} (username, attribute, op, value) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(sql, (user.username, reply.attribute, reply.op, reply.value))

            for group in user.groups:
                sql = f"INSERT INTO {RADUSERGROUP} (username, groupname, priority) VALUES (%s, %s, %s)"
                db_cursor.execute(sql, (user.username, group.groupname, group.priority))

    def set(
        self,
        username: str,
        new_checks: list[AttributeOpValue] | None = None,
        new_replies: list[AttributeOpValue] | None = None,
        new_groups: list[UserGroup] | None = None,
    ):
        with closing(self.db_connection.cursor()) as db_cursor:
            if new_checks is not None:
                db_cursor.execute(f"DELETE FROM {RADCHECK} WHERE username = %s", (username,))
                for check in new_checks:
                    sql = f"INSERT INTO {RADCHECK} (username, attribute, op, value) VALUES (%s, %s, %s, %s)"
                    db_cursor.execute(sql, (username, check.attribute, check.op, check.value))

            if new_replies is not None:
                db_cursor.execute(f"DELETE FROM {RADREPLY} WHERE username = %s", (username,))
                for reply in new_replies:
                    sql = f"INSERT INTO {RADREPLY} (username, attribute, op, value) VALUES (%s, %s, %s, %s)"
                    db_cursor.execute(sql, (username, reply.attribute, reply.op, reply.value))

            if new_groups is not None:
                db_cursor.execute(f"DELETE FROM {RADUSERGROUP} WHERE username = %s", (username,))
                for group in new_groups:
                    sql = f"INSERT INTO {RADUSERGROUP} (username, groupname, priority) VALUES (%s, %s, %s)"
                    db_cursor.execute(sql, (username, group.groupname, group.priority))

    def remove(self, username: str):
        with closing(self.db_connection.cursor()) as db_cursor:
            db_cursor.execute(f"DELETE FROM {RADCHECK} WHERE username = %s", (username,))
            db_cursor.execute(f"DELETE FROM {RADREPLY} WHERE username = %s", (username,))
            db_cursor.execute(f"DELETE FROM {RADUSERGROUP} WHERE username = %s", (username,))


class GroupRepository(BaseRepository):
    def __init__(self, db_connection):
        super().__init__(db_connection)

    def exists(self, groupname: str) -> bool:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""SELECT COUNT(DISTINCT groupname) FROM {RADGROUPCHECK} WHERE groupname = %s
                UNION SELECT COUNT(DISTINCT groupname) FROM {RADGROUPREPLY} WHERE groupname = %s
                UNION SELECT COUNT(DISTINCT groupname) FROM {RADUSERGROUP} WHERE groupname = %s"""
            db_cursor.execute(sql, (groupname, groupname, groupname))
            counts = [count for (count,) in db_cursor.fetchall()]
            return sum(counts) > 0

    def find_all_groupnames(self) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""SELECT DISTINCT groupname FROM {RADGROUPCHECK}
                UNION SELECT DISTINCT groupname FROM {RADGROUPREPLY}
                UNION SELECT DISTINCT groupname FROM {RADUSERGROUP}"""
            db_cursor.execute(sql)
            groupnames = [groupname for (groupname,) in db_cursor.fetchall()]
            return groupnames

    def find_groupnames(self, from_groupname: str | None = None) -> list[str]:
        if not from_groupname:
            return self._find_first_groupnames()
        return self._find_next_groupnames(from_groupname)

    def _find_first_groupnames(self) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""
                SELECT groupname FROM (
                        SELECT DISTINCT groupname FROM {RADGROUPCHECK}
                  UNION SELECT DISTINCT groupname FROM {RADGROUPREPLY}
                  UNION SELECT DISTINCT groupname FROM {RADUSERGROUP}
                ) g ORDER BY groupname LIMIT {PER_PAGE}
            """
            db_cursor.execute(sql)
            groupnames = [groupname for (groupname,) in db_cursor.fetchall()]
            return groupnames

    def _find_next_groupnames(self, from_groupname: str) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""
                SELECT groupname FROM (
                        SELECT DISTINCT groupname FROM {RADGROUPCHECK}
                  UNION SELECT DISTINCT groupname FROM {RADGROUPREPLY}
                  UNION SELECT DISTINCT groupname FROM {RADUSERGROUP}
                ) g WHERE groupname > %s ORDER BY groupname LIMIT {PER_PAGE}
            """
            db_cursor.execute(sql, (from_groupname,))
            groupnames = [groupname for (groupname,) in db_cursor.fetchall()]
            return groupnames

    def has_users(self, groupname: str) -> bool:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"SELECT COUNT(DISTINCT username) FROM {RADUSERGROUP} WHERE groupname = %s"
            db_cursor.execute(sql, (groupname,))
            (count,) = db_cursor.fetchone()
            return count > 0

    def find_one(self, groupname: str) -> Group | None:
        if not self.exists(groupname):
            return None

        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"SELECT attribute, op, value FROM {RADGROUPCHECK} WHERE groupname = %s"
            db_cursor.execute(sql, (groupname,))
            checks = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f"SELECT attribute, op, value FROM {RADGROUPREPLY} WHERE groupname = %s"
            db_cursor.execute(sql, (groupname,))
            replies = [AttributeOpValue(attribute=a, op=o, value=v) for a, o, v in db_cursor.fetchall()]

            sql = f"SELECT username, priority FROM {RADUSERGROUP} WHERE groupname = %s"
            db_cursor.execute(sql, (groupname,))
            users = [GroupUser(username=u, priority=p) for u, p in db_cursor.fetchall()]

            return Group(groupname=groupname, checks=checks, replies=replies, users=users)

    def add(self, group: Group):
        with closing(self.db_connection.cursor()) as db_cursor:
            for check in group.checks:
                sql = f"INSERT INTO {RADGROUPCHECK} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(sql, (group.groupname, check.attribute, check.op, check.value))

            for reply in group.replies:
                sql = f"INSERT INTO {RADGROUPREPLY} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)"
                db_cursor.execute(sql, (group.groupname, reply.attribute, reply.op, reply.value))

            for user in group.users:
                sql = f"INSERT INTO {RADUSERGROUP} (groupname, username, priority) VALUES (%s, %s, %s)"
                db_cursor.execute(sql, (group.groupname, user.username, user.priority))

    def set(
        self,
        groupname: str,
        new_checks: list[AttributeOpValue] | None = None,
        new_replies: list[AttributeOpValue] | None = None,
        new_users: list[GroupUser] | None = None,
    ):
        with closing(self.db_connection.cursor()) as db_cursor:
            if new_checks is not None:
                db_cursor.execute(f"DELETE FROM {RADGROUPCHECK} WHERE groupname = %s", (groupname,))
                for check in new_checks:
                    sql = f"INSERT INTO {RADGROUPCHECK} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)"
                    db_cursor.execute(sql, (groupname, check.attribute, check.op, check.value))

            if new_replies is not None:
                db_cursor.execute(f"DELETE FROM {RADGROUPREPLY} WHERE groupname = %s", (groupname,))
                for reply in new_replies:
                    sql = f"INSERT INTO {RADGROUPREPLY} (groupname, attribute, op, value) VALUES (%s, %s, %s, %s)"
                    db_cursor.execute(sql, (groupname, reply.attribute, reply.op, reply.value))

            if new_users is not None:
                db_cursor.execute(f"DELETE FROM {RADUSERGROUP} WHERE groupname = %s", (groupname,))
                for user in new_users:
                    sql = f"INSERT INTO {RADUSERGROUP} (groupname, username, priority) VALUES (%s, %s, %s)"
                    db_cursor.execute(sql, (groupname, user.username, user.priority))

    def remove(self, groupname: str):
        with closing(self.db_connection.cursor()) as db_cursor:
            db_cursor.execute(f"DELETE FROM {RADGROUPCHECK} WHERE groupname = %s", (groupname,))
            db_cursor.execute(f"DELETE FROM {RADGROUPREPLY} WHERE groupname = %s", (groupname,))
            db_cursor.execute(f"DELETE FROM {RADUSERGROUP} WHERE groupname = %s", (groupname,))


class NasRepository(BaseRepository):
    def __init__(self, db_connection):
        super().__init__(db_connection)

    def exists(self, nasname: str) -> bool:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"SELECT COUNT(DISTINCT nasname) FROM {NAS} WHERE nasname = %s"
            db_cursor.execute(sql, (nasname,))
            (count,) = db_cursor.fetchone()
            return count > 0

    def find_all_nasnames(self) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"SELECT DISTINCT nasname FROM {NAS}"
            db_cursor.execute(sql)
            nasnames = [nasname for (nasname,) in db_cursor.fetchall()]
            return nasnames

    def find_nasnames(self, from_nasname: str | None = None) -> list[str]:
        if not from_nasname:
            return self._find_first_nasnames()
        return self._find_next_nasnames(from_nasname)

    def _find_first_nasnames(self) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""SELECT DISTINCT nasname FROM {NAS}
                      ORDER BY nasname LIMIT {PER_PAGE}"""
            db_cursor.execute(sql)
            nasnames = [nasname for (nasname,) in db_cursor.fetchall()]
            return nasnames

    def _find_next_nasnames(self, from_nasname: str) -> list[str]:
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"""SELECT DISTINCT nasname FROM {NAS}
                      WHERE nasname > %s ORDER BY nasname LIMIT {PER_PAGE}"""
            db_cursor.execute(sql, (from_nasname,))
            nasnames = [nasname for (nasname,) in db_cursor.fetchall()]
            return nasnames

    def find_one(self, nasname: str) -> Nas | None:
        if not self.exists(nasname):
            return None

        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"SELECT nasname, shortname, secret FROM {NAS} WHERE nasname = %s"
            db_cursor.execute(sql, (nasname,))
            n, sh, se = db_cursor.fetchone()
            return Nas(nasname=n, shortname=sh, secret=se)

    def add(self, nas: Nas):
        with closing(self.db_connection.cursor()) as db_cursor:
            sql = f"INSERT INTO {NAS} (nasname, shortname, secret) VALUES (%s, %s, %s)"
            db_cursor.execute(sql, (nas.nasname, nas.shortname, nas.secret))

    def set(self, nasname: str, new_shortname: str | None = None, new_secret: str | None = None):
        with closing(self.db_connection.cursor()) as db_cursor:
            if new_shortname is not None:
                sql = f"UPDATE {NAS} SET shortname = %s WHERE nasname = %s"
                db_cursor.execute(sql, (new_shortname, nasname))

            if new_secret is not None:
                sql = f"UPDATE {NAS} SET secret = %s WHERE nasname = %s"
                db_cursor.execute(sql, (new_secret, nasname))

    def remove(self, nasname: str):
        with closing(self.db_connection.cursor()) as db_cursor:
            db_cursor.execute(f"DELETE FROM {NAS} WHERE nasname = %s", (nasname,))
