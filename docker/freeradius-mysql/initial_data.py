from database import db_connection, db_tables
from pyfreeradius import User, Group, Nas, AttributeOpValue, UserGroup
from pyfreeradius import UserRepository, GroupRepository, NasRepository

# Load the FreeRADIUS repositories
user_repo = UserRepository(db_connection, db_tables)
group_repo = GroupRepository(db_connection, db_tables)
nas_repo = NasRepository(db_connection, db_tables)

# Add some NASes
n1 = Nas(nasname='3.3.3.3', shortname='my-super-nas', secret='my-super-secret')
n2 = Nas(nasname='4.4.4.4', shortname='my-other-nas', secret='my-other-secret')
if not nas_repo.exists(n1.nasname) and \
   not nas_repo.exists(n2.nasname):
    nas_repo.add(n1)
    nas_repo.add(n2)

# Add some groups
g1 = Group(groupname='100m', replies=[AttributeOpValue(attribute='Filter-Id', op=':=', value='100m')])
g2 = Group(groupname='200m', replies=[AttributeOpValue(attribute='Filter-Id', op=':=', value='200m')])
if not group_repo.exists(g1.groupname) and \
   not group_repo.exists(g2.groupname):
    group_repo.add(g1)
    group_repo.add(g2)

# Add some users
u1 = User(
    username='bob',
    groups=[UserGroup(groupname=g1.groupname)],
    checks=[AttributeOpValue(attribute='Cleartext-Password', op=':=', value='bob-pass')],
    replies=[AttributeOpValue(attribute='Framed-IP-Address', op=':=', value='10.0.0.1'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.1.0/24'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.2.0/24'),
             AttributeOpValue(attribute='Huawei-Vpn-Instance', op=':=', value='bob-vrf')]
)
u2 = User(
    username='alice@adsl',
    groups=[UserGroup(groupname=g1.groupname)],
    checks=[AttributeOpValue(attribute='Cleartext-Password', op=':=', value='alice-pass')],
    replies=[AttributeOpValue(attribute='Framed-IP-Address', op=':=', value='10.0.0.2'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.1.0/24'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.2.0/24'),
             AttributeOpValue(attribute='Huawei-Vpn-Instance', op=':=', value='alice-vrf')]
)
u3 = User(
    username='eve',
    groups=[UserGroup(groupname=g1.groupname, priority=1), UserGroup(groupname=g2.groupname, priority=2)],
    checks=[AttributeOpValue(attribute='Cleartext-Password', op=':=', value='eve-pass')],
    replies=[AttributeOpValue(attribute='Framed-IP-Address', op=':=', value='10.0.0.3'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.1.0/24'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.2.0/24'),
             AttributeOpValue(attribute='Huawei-Vpn-Instance', op=':=', value='eve-vrf')]
)
u4 = User(
    username='oscar@wil.de',
    checks=[AttributeOpValue(attribute='Cleartext-Password', op=':=', value='oscar-pass')],
    replies=[AttributeOpValue(attribute='Framed-IP-Address', op=':=', value='10.0.0.4'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.1.0/24'),
             AttributeOpValue(attribute='Framed-Route', op='+=', value='192.168.2.0/24'),
             AttributeOpValue(attribute='Huawei-Vpn-Instance', op=':=', value='oscar-vrf')]
)
if not user_repo.exists(u1.username) and \
   not user_repo.exists(u2.username) and \
   not user_repo.exists(u3.username) and \
   not user_repo.exists(u4.username) and \
   group_repo.exists(g1.groupname)   and \
   group_repo.exists(g2.groupname):
    user_repo.add(u1)
    user_repo.add(u2)
    user_repo.add(u3)
    user_repo.add(u4)
