from database import db_connection, db_tables
from pyfreeradius import User, Group, Nas, AttributeOpValue, UserGroup
from pyfreeradius import UserRepository, GroupRepository, NasRepository

# Load the FreeRADIUS repositories
user_repo = UserRepository(db_connection, db_tables)
group_repo = GroupRepository(db_connection, db_tables)
nas_repo = NasRepository(db_connection, db_tables)

# Add some NASes
n1 = Nas(nasname='1.1.1.1', shortname='my-super-nas', secret='my-super-secret')
n2 = Nas(nasname='2.2.2.2', shortname='my-other-nas', secret='my-other-secret')
if not nas_repo.exists(n1.nasname) and \
   not nas_repo.exists(n2.nasname):
    nas_repo.add(n1)
    nas_repo.add(n2)

# Add some groups
g1 = Group(groupname='my-super-group', replies=[AttributeOpValue(attribute='Filter-Id', op=':=', value='100m')])
g2 = Group(groupname='my-other-group', replies=[AttributeOpValue(attribute='Filter-Id', op=':=', value='200m')])
if not group_repo.exists(g1.groupname) and \
   not group_repo.exists(g2.groupname):
    group_repo.add(g1)
    group_repo.add(g2)

# Add some users
u1 = User(
    username='my-super-user',
    groups=[UserGroup(groupname=g1.groupname)],
    checks=[AttributeOpValue(attribute='Cleartext-Password', op=':=', value='my-super-pass')],
    replies=[AttributeOpValue(attribute='Framed-IP-Address', op=':=', value='10.0.0.1'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.1.0/24'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.2.0/24'),
             AttributeOpValue(attribute='Huawei-Vpn-Instance', op=':=', value='my-super-vrf')]
)
u2 = User(
    username='my-other-user',
    checks=[AttributeOpValue(attribute='Cleartext-Password', op=':=', value='my-other-pass')],
    replies=[AttributeOpValue(attribute='Framed-IP-Address', op=':=', value='10.0.0.2'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.1.0/24'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.2.0/24'),
             AttributeOpValue(attribute='Huawei-Vpn-Instance', op=':=', value='my-other-vrf')]
)
if not user_repo.exists(u1.username) and \
   not user_repo.exists(u2.username) and \
   group_repo.exists(g1.groupname):
    user_repo.add(u1)
    user_repo.add(u2)

# Some printing
print(nas_repo.find_all_nasnames())
print(user_repo.find_all_usernames())
print(group_repo.find_all_groupnames())
print(group_repo.has_users(g1.groupname)) # will print True
print(group_repo.has_users(g2.groupname)) # will print False

# Remove what we added
nas_repo.remove(n1.nasname)
nas_repo.remove(n2.nasname)
user_repo.remove(u1.username)
user_repo.remove(u2.username)

if not group_repo.has_users(g1.groupname) and \
   not group_repo.has_users(g2.groupname):
    group_repo.remove(g1.groupname)
    group_repo.remove(g2.groupname)
