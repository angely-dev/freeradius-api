[![Python 3.7+](https://img.shields.io/badge/Python-3.7+-success.svg)](https://www.python.org/downloads/release/python-370)
[![License MIT](https://img.shields.io/badge/License-MIT-success.svg)](https://opensource.org/licenses/MIT)

* [What is this project?](#what-is-this-project)
* [What it is NOT?](#what-it-is-not)
* [Quick demo](#quick-demo)
* [How To](#how-to)
  * [Using Docker](#using-docker) (for testing only)
  * [Using a venv](#using-a-venv)
* [Conceptual approach](#conceptual-approach)
  * [Domain-Driven Design](#domain-driven-design-ddd) (repository pattern)
  * [Class diagram](#class-diagram)
 
# What is this project?

A REST API on top of the [FreeRADIUS](https://freeradius.org) database schema for automation and integration purposes.

* It provides a bit of logic and [#semantic](https://github.com/angely-dev/freeradius-api#semantic) to ensure some data consistency
* It aims to be KISS so that it can be plugged or forked for adding more business logic

Based on [Pydantic](https://github.com/pydantic/pydantic) and [FastAPI](https://github.com/tiangolo/fastapi). But you can stick with the [`pyfreeradius`](https://github.com/angely-dev/freeradius-api/blob/master/src/pyfreeradius.py) module and build your own API over it.

> **Why Python?** Because it tends to be the de-facto standard in network automation, yet the model-centric approach taken here allows for other implementations. Feel free to adapt!

> **What database support?** It works with any DB-API 2.0 ([PEP 249](https://peps.python.org/pep-0249/)) enabled driver: `pymysql`, `pymssql`, `psycopg2`, `sqlite3`, etc. Just one line has to be changed to load the appropriate one.

![image](https://user-images.githubusercontent.com/4362224/202903625-096d00f4-957e-4eed-8e35-c7489673c4be.png)

# What it is NOT?

* A dumb CRUD API on top of the FreeRADIUS database schema
* A means to run the AAA server logic through HTTP (covered by the native [rest](https://github.com/FreeRADIUS/freeradius-server/blob/release_3_2_1/raddb/mods-available/rest) module)

# Quick demo

## Using the module

The `pyfreeradius` module works with Python objects.

See [#module-only](#module-only).

## Using the API

The API works with JSON objects.

Here is a demo below using `curl` instead of the Web UI:

* Get all NASes, users and groups:

```bash
$ curl -X 'GET' http://localhost:8000/nas
[
    "3.3.3.3",
    "4.4.4.4"
]
```
```bash
$ curl -X 'GET' http://localhost:8000/users
[
    "bob",
    "alice@adsl",
    "eve",
    "oscar@wil.de"
]
```
```bash
$ curl -X 'GET' http://localhost:8000/groups
[
    "100m",
    "200m"
]
```

* Get a specific NAS, user or group:

```bash
$ curl -X 'GET' http://localhost:8000/nas/3.3.3.3
{
    "nasname": "3.3.3.3",
    "shortname": "my-super-nas",
    "secret": "my-super-secret"
}
```
```bash
$ curl -X 'GET' http://localhost:8000/users/eve
{
    "username": "eve",
    "checks": [
        {
            "attribute": "Cleartext-Password",
            "op": ":=",
            "value": "eve-pass"
        }
    ],
    "replies": [
        {
            "attribute": "Framed-IP-Address",
            "op": ":=",
            "value": "10.0.0.3"
        },
        {
            "attribute": "Framed-Route",
            "op": "+=",
            "value": "192.168.1.0/24"
        },
        {
            "attribute": "Framed-Route",
            "op": "+=",
            "value": "192.168.2.0/24"
        },
        {
            "attribute": "Huawei-Vpn-Instance",
            "op": ":=",
            "value": "eve-vrf"
        }
    ],
    "groups": [
        {
            "groupname": "100m",
            "priority": 1
        },
        {
            "groupname": "200m",
            "priority": 2
        }
    ]
}
```
```bash
$ curl -X 'GET' http://localhost:8000/groups/100m
{
    "groupname": "100m",
    "checks": [],
    "replies": [
        {
            "attribute": "Filter-Id",
            "op": ":=",
            "value": "100m"
        }
    ],
    "users": [
        {
            "username": "bob",
            "priority": 1
        },
        {
            "username": "alice@adsl",
            "priority": 1
        },
        {
            "username": "eve",
            "priority": 1
        }
    ]
}
```

* Post a NAS, a user or a group:

```bash
curl -X 'POST' \
  'http://localhost:8000/nas' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "nasname": "5.5.5.5",
  "shortname": "my-nas",
  "secret": "my-secret"
}'
```
```bash
curl -X 'POST' \
  'http://localhost:8000/users' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "my-user@my-realm",
  "checks": [
    {
      "attribute": "Cleartext-Password",
      "op": ":=",
      "value": "my-pass"
    }
  ],
  "replies": [
    {
      "attribute": "Framed-IP-Address",
      "op": ":=",
      "value": "192.168.0.1"
    },
    {
      "attribute": "Huawei-Vpn-Instance",
      "op": ":=",
      "value": "my-vrf"
    }
  ]
}'
```
```bash
curl -X 'POST' \
  'http://localhost:8000/groups' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "groupname": "300m",
  "replies": [
    {
      "attribute": "Filter-Id",
      "op": ":=",
      "value": "300m"
    }
  ]
}'
```

* Delete a NAS, a user or a group:

```bash
curl -X 'DELETE' http://localhost:8000/nas/5.5.5.5
curl -X 'DELETE' http://localhost:8000/users/my-user@my-realm
curl -X 'DELETE' http://localhost:8000/groups/300m
```

# How To

**An instance of the FreeRADIUS server is NOT needed for testing.** The focus is on the FreeRADIUS database. As long as you have one, the API can run on a Python environment.

## Using Docker

I made a full Docker stack for testing purposes that should run "as is". It includes the API and a MySQL database with some initial data ????

If you already have a FreeRADIUS database (either local or remote) or if you fear Docker, you can skip this section ????

```bash
wget https://github.com/angely-dev/freeradius-api/archive/refs/heads/master.zip
unzip master.zip
cd freeradius-api-master/docker
#
docker compose up -d
```

Docker output should be like this:

```bash
Creating network "docker_default" with the default driver
Creating volume "docker_myvol" with default driver
Pulling mydb (mysql:)...
[???]
Building radapi
[???]
Pulling myadmin (phpmyadmin:)...
[???]
Creating docker_mydb_1 ... done
Creating docker_myadmin_1 ... done
Creating docker_radapi_1  ... done
```

Then go to: http://localhost:8000/docs

## Using a venv

* Get the project and set the venv:

```bash
wget https://github.com/angely-dev/freeradius-api/archive/refs/heads/master.zip
unzip master.zip
cd freeradius-api-master
#
virtualenv venv
source venv/bin/activate
```

* Edit [`requirements.txt`](https://github.com/angely-dev/freeradius-api/blob/master/requirements.txt) to set the DB driver depending on your database system (MySQL, PostgreSQL, etc.):

```py
# Uncomment the appropriate line to load the DB-API 2.0 (PEP 249) enabled driver
mysql-connector-python
#pymysql
#pymssql
#psycopg2
#sqllite3
#oracledb
#<DRIVER>
```

* Then install the requirements:

```bash
pip install -r requirements.txt
```

* Edit [`src/database.py`](https://github.com/angely-dev/freeradius-api/blob/master/src/database.py) to set your DB settings (driver, connection and table names):

```py
from pyfreeradius import RadTables

# Uncomment the appropriate line to load the DB-API 2.0 (PEP 249) enabled driver
from mysql.connector import connect
#from pymysql import connect
#from pymssql import connect
#from psycopg2 import connect
#from sqllite3 import connect
#from oracledb import connect
#from <DRIVER> import connect

# DB connection and table names
db_connection = connect(user='raduser', password='radpass', host='mydb', database='raddb')
db_tables = RadTables()
```

* Optionally, if you use different tables names in your FreeRADIUS database:

```py
db_tables = RadTables(
    radcheck='my-radcheck',
    radreply='my-radreply',
    radgroupcheck='my-radgroupcheck',
    radgroupreply='my-radgroupreply',
    radusergroup='my-radusergroup',
    nas='my-nas'
)
```

* That's it! Now run the API and play with it live! All thanks to [FastAPI](https://github.com/tiangolo/fastapi) generating the OpenAPI specs and embedding [Swagger UI](https://github.com/swagger-api/swagger-ui) ????

```bash
cd src
uvicorn api:app
INFO:     Started server process [12884]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

* Then go to: http://localhost:8000/docs

![image](https://user-images.githubusercontent.com/4362224/202903625-096d00f4-957e-4eed-8e35-c7489673c4be.png)

### Module only

You are free to use the core module without the API.

The steps are the exact same except you don't run the API at the end.
I did provide a [`sample.py`](https://github.com/angely-dev/freeradius-api/blob/master/src/sample.py) file:

> **Note:** the term *repository* refers to the Repository pattern. See the [#conceptual-approach](#conceptual-approach).

```py
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
```

Corresponding output:

```bash
$ python3 sample.py
['1.1.1.1', '2.2.2.2']
['my-super-user', 'my-other-user']
['my-super-group', 'my-other-group']
True
False
```

?????? If you use the `pyfreeradius` module directly, be cautious with the logic you implement over it (since none is implemented by the repositories and very little by the Pydantic models). Without any guards, this can lead to invalid states in the database (e.g., user added twice, belonging to a non-existing group). As a starting point, you may want to use the logic contained in the `sample.py` file (.e.g., `exists`, `has_users`).

### Unit tests

If desired, feel free to run the unit tests to ensure your install is fully working:

```bash
$ python3 -m unittest test.py
.....
----------------------------------------------------------------------
Ran 5 tests in 0.137s

OK
```

And optionally, for measuring code coverage:

```bash
$ pip install coverage

# First we (re)run the unit tests
$ coverage run -m unittest test.py
.....
----------------------------------------------------------------------
Ran 5 tests in 0.095s

OK

# Then we generate the CLI report
$ coverage report
Name              Stmts   Miss  Cover
-------------------------------------
database.py           5      0   100%
pyfreeradius.py     204      0   100%
test.py              70      0   100%
-------------------------------------
TOTAL               279      0   100%

# We can also generate a more detailed HTML report
$ coverage html
Wrote HTML report to htmlcov/index.html
```

The HTML report is then browsable:

![image](https://user-images.githubusercontent.com/4362224/202913672-2e8205f5-a0ca-409f-bad6-14a93191972f.png)

# Conceptual approach

You may be interested in the model-centric approach taken (or you may not).

The implementation is fairly easy but it is good to know it conforms to some pattern.

## Domain-Driven Design (DDD)

I found similarities with the DDD and especially the **Repository pattern.** It is a well-known pattern, yet often poorly applied, particularly in CRUD apps where there is a one-to-one mapping between entities and the database. In that case, the Repository just adds an extra layer for nothing really. I found it well-suited here because the "raw" database schema differs from the object-oriented or the "business" view of the Domain (the subject area).

> A REPOSITORY represents all objects of a certain type as a conceptual set **(usually emulated).** It acts like a collection, except with more elaborate querying capability. Objects of the appropriate type are added and removed, and the machinery behind the REPOSITORY inserts them or deletes them from the database. **The easiest REPOSITORY to build has hard-coded queries with specific parameters.** These queries can be various: retrieving an ENTITY by its identity (???)
>
> ??? Domain-Driven Design: Tackling Complexity in the Heart of Software. Eric Evans

Repositories are responsible for mapping Domain Objects to the database where they get flattened in some way:

![image](https://user-images.githubusercontent.com/4362224/202743771-07877b22-da82-4967-8bd5-1e62bb2f1e9a.png)

The Domain Services (corresponding to the `api.py` file) call the repositories to implement the Domain Logic which cannot fit in the Domain Objects directly (typically, when fetching data from different repositories is required for validation purpose). As per the DDD, the Domain Objects are classified this way:

* **Entities:** they have an identity and a lifecycle interest (`User`, `Group` and `Nas`)
* **Value Objects:** they have no conceptual identity and are Entity characteristics (`AttributeOpValue`)
* **Aggregate Root:** set of Entities and Value Objects with a well-defined boundary, the root being an Entity (a repository is then designed for each Aggregate Root)

`User` and `Group` are Aggregate Roots (they both aggregate check and reply attributes). `Nas` is also an Aggregate Root (it has its own boundary). Moreover, `User` and `Group` being linked together, this will produce some kind of association-class. In such a case, it is preferable to reference aggregates "by identity" to prevent boundary crossing:

> Prefer references to external aggregates only by their globally unique identity, not by holding a direct object reference (or ???pointer???).
>
> ??? [Effective Aggregate Design, Part II: Making Aggregates Work Together.](https://www.dddcommunity.org/library/vernon_2011/) Vaughn Vernon

## Class diagram

The UML class diagram may help to bring semantic and an object-oriented view of the FreeRADIUS database schema (therefore, this is NOT a one-to-one mapping with that schema).

![uml-class-diagram](https://user-images.githubusercontent.com/4362224/202876207-bc272618-a8d8-407d-a5fe-a523aaf492e8.png)

As represented, the `AttributeOpValue` class should be ideally subclassed since the sets of supported attributes and operators differ between the subclasses. This could be implemented with Enums. However, for simplicity, I decided not to do it, mainly because it would have meant reinventing (or integrating in some way) the RADIUS dictionaries.

Also, I limited the `Nas` attributes but you can add more if needed, .e.g., `type`, `community`, etc.

### Semantic

The diagram must be interpreted as follows:

* A `User` may have `Check` or `Reply` attributes ??? if the user is deleted, so are its attributes
* A `Group` may have `Check` or `Reply` attributes ??? if the group is deleted, so are its attributes
* A `User` may belong to multiple `Group` ??? if the user is deleted, so are its belonging to groups
* A `Group` may contain multiple `User` ??? if the group is deleted, so are its belonging to users

> To prevent accidental deletion however (when a group still contains legit users), we can think of a flag like `ignoreUsers` to be passed.

* User groups are ordered by a `priority` which semantic is fully documented in the [rlm_sql](https://wiki.freeradius.org/modules/Rlm_sql) module
* The `Nas` could be a standalone class. Alternatively, we can consider it depends on `User` as NASes perform AAA requests on them. This choice will have no consequence on the implementation as per the UML standard:

> The presence of Dependency relationships in a model does not have any runtime semantic implications.

### Some common sense (expressed by the property modifiers)

* A `username` is like an ID (two users cannot share the same one) ??? hence the use of `{id}`
* A `groupname` is like an ID (two groups cannot share the same one) ??? hence the use of `{id}`
* A `nasname` is like an ID (two NASes cannot share the same one) ??? hence the use of `{id}`
* A `User` cannot belong twice to the same `Group` ??? hence the use of `{unique}`
* A `Group` cannot contain twice to the same `User` ??? hence the use of `{unique}`

### Some more constraints (not graphically represented)

* A `Group` must have at least one `Check` or one `Reply` attribute
* A `User` must have at least one `Check` or one `Reply` attribute, or must belong to at least one `Group`
* Otherwise, they won't really exist in the database as per the FreeRADIUS schema

Theoretically, a `Group` may exist without any attributes but with users in it, though I don't see any practical use.
