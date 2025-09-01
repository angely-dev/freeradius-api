import os
import time

from pyfreeradius.models import AttributeOpValue, Group, Nas, User, UserGroup
from pyfreeradius.repositories import GroupRepository, NasRepository, UserRepository
from src.database import db_connect

# This script populate "fake" data into the database
# It gives users a
# Check if we should populate development data
# Only populate in development environment
env = os.getenv("APP_ENV", "development")
populate_dev_data = env.lower() in ["dev", "development"]

def connect_with_retry(max_retries=10, delay=5):
    """Attempt to connect to the database with retries."""
    for attempt in range(max_retries):
        try:
            db_connection = db_connect()
            # Test the connection
            db_connection.ping()
            return db_connection
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise

if populate_dev_data:
    # Load the FreeRADIUS repositories with retry mechanism
    try:
        db_connection = connect_with_retry()
        user_repo = UserRepository(db_connection)
        group_repo = GroupRepository(db_connection)
        nas_repo = NasRepository(db_connection)

        # Add some NASes
        n1 = Nas(nasname="3.3.3.3", shortname="my-super-nas", secret="my-super-secret")
        n2 = Nas(nasname="4.4.4.4", shortname="my-other-nas", secret="my-other-secret")
        if not nas_repo.exists(n1.nasname) and not nas_repo.exists(n2.nasname):
            nas_repo.add(n1)
            nas_repo.add(n2)

        # Add some groups
        g1 = Group(groupname="100m", replies=[AttributeOpValue(attribute="Filter-Id", op=":=", value="100m")])
        g2 = Group(groupname="200m", replies=[AttributeOpValue(attribute="Filter-Id", op=":=", value="200m")])
        if not group_repo.exists(g1.groupname) and not group_repo.exists(g2.groupname):
            group_repo.add(g1)
            group_repo.add(g2)

        # Add some users
        u1 = User(
            username="bob",
            groups=[UserGroup(groupname=g1.groupname)],
            checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="bob-pass")],
            replies=[
                AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.1"),
                AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24"),
                AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24"),
                AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="bob-vrf"),
            ],
        )
        u2 = User(
            username="alice@adsl",
            groups=[UserGroup(groupname=g1.groupname)],
            checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="alice-pass")],
            replies=[
                AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.2"),
                AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24"),
                AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24"),
                AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="alice-vrf"),
            ],
        )
        u3 = User(
            username="eve",
            groups=[UserGroup(groupname=g1.groupname, priority=1), UserGroup(groupname=g2.groupname, priority=2)],
            checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="eve-pass")],
            replies=[
                AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.3"),
                AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24"),
                AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24"),
                AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="eve-vrf"),
            ],
        )
        u4 = User(
            username="oscar@wil.de",
            checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="oscar-pass")],
            replies=[
                AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.4"),
                AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24"),
                AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24"),
                AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="oscar-vrf"),
            ],
        )
        if (
            not user_repo.exists(u1.username)
            and not user_repo.exists(u2.username)
            and not user_repo.exists(u3.username)
            and not user_repo.exists(u4.username)
            and group_repo.exists(g1.groupname)
            and group_repo.exists(g2.groupname)
        ):
            user_repo.add(u1)
            user_repo.add(u2)
            user_repo.add(u3)
            user_repo.add(u4)

        db_connection.commit()
        db_connection.close()
        print("Development data populated successfully")
    except Exception as e:
        print(f"Failed to populate development data: {e}")
        # We don"t want to crash the entire application if we can"t populate data
        # The API should still work without the initial data
else:
    print("Skipping development data population in non-development environment")
