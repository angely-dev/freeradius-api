[![python](https://img.shields.io/badge/python-3.10+-success.svg)](https://devguide.python.org/versions)
[![license](https://img.shields.io/badge/license-MIT-success.svg)](https://opensource.org/licenses/MIT)

---

_Doc is about to be updated!_

---

* [What is this project?](#what-is-this-project)
* [What it is NOT?](#what-it-is-not)
* [Quick demo](#quick-demo)
* [How To](#how-to)
  * [Using Docker](#using-docker) (for testing only)
  * [Using a venv](#using-a-venv)
* [Keyset pagination](#keyset-pagination)
* [API authentication](#api-authentication) (optional)
* [Conceptual approach](#conceptual-approach)
  * [Domain-Driven Design](#domain-driven-design-ddd) (repository pattern)
  * [Class diagram](#class-diagram)

# What is this project?

A lightweight REST API on top of the [FreeRADIUS](https://freeradius.org) database schema for automation and integration purposes.

* It provides a bit of logic and [#semantic](https://github.com/angely-dev/freeradius-api#semantic) to ensure some data consistency
* It aims to be KISS so that it can be plugged or forked for adding more business logic

Based on [Pydantic](https://github.com/pydantic/pydantic) and [FastAPI](https://github.com/tiangolo/fastapi). But you can stick with the [`pyfreeradius`](https://github.com/angely-dev/freeradius-api/blob/master/src/pyfreeradius) package and build your own API over it.

> **Why Python?** Because it tends to be the de-facto standard in network automation, yet the model-centric approach taken here allows for other implementations. Feel free to adapt!

> **What database support?** It works with any DB-API 2.0 ([PEP 249](https://peps.python.org/pep-0249/)) enabled driver: `pymysql`, `pymssql`, `psycopg2`, `sqlite3`, etc. Just one line has to be changed to load the appropriate one.

![image](https://user-images.githubusercontent.com/4362224/202903625-096d00f4-957e-4eed-8e35-c7489673c4be.png)

# What it is NOT?

* A dumb CRUD API on top of the FreeRADIUS database schema
* A means to run the AAA server logic through HTTP (covered by the native [rest](https://github.com/FreeRADIUS/freeradius-server/blob/release_3_2_1/raddb/mods-available/rest) module)

# Quick demo

## Using the package

The `pyfreeradius` package works with Python objects.

See [#package-only](#package-only).

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

> **Reminder:**
> * When a user is deleted, so are its attributes and its belonging to groups
> * When a group is deleted, so are its attributes and its belonging to users ([if `ignore_users` is set](https://github.com/angely-dev/freeradius-api/blob/v1.4.0/src/api.py#L137-L139))
>
> See [#semantic](https://github.com/angely-dev/freeradius-api#semantic).

# How To

**An instance of the FreeRADIUS server is NOT needed for testing.** The focus is on the FreeRADIUS database. As long as you have one, the API can run on a Python environment.

## Using Docker

I made a full Docker stack for testing purposes that should run "as is". It includes the API and a MySQL database with some initial data 😊

If you already have a FreeRADIUS database (either local or remote) or if you fear Docker, you can skip this section 🚀

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
[…]
Building radapi
[…]
Pulling myadmin (phpmyadmin:)...
[…]
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
python3 -m venv venv
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

* Edit [`src/settings.py`](https://github.com/angely-dev/freeradius-api/blob/master/src/settings.py) to set your DB settings (driver, connection and table names):

```py
# Uncomment the appropriate line matching your DB-API 2.0 (PEP 249) enabled driver
DB_DRIVER = "mysql.connector"
# DB_DRIVER = "pymysql"
# DB_DRIVER = "pymssql"
# DB_DRIVER = "psycopg2"
# DB_DRIVER = "sqllite3"
# DB_DRIVER = "oracledb"
# DB_DRIVER = "<DRIVER>"

# Database connection settings
DB_NAME = "raddb"
DB_USER = "raduser"
DB_PASS = "radpass"
DB_HOST = "mydb"

# Database table names
RADCHECK = "radcheck"
RADREPLY = "radreply"
RADGROUPCHECK = "radgroupcheck"
RADGROUPREPLY = "radgroupreply"
RADUSERGROUP = "radusergroup"
NAS = "nas"
```

* You can also customize the number of results per page:

```py
# Number of results per page for pagination
PER_PAGE = 100
```

* Finally, you may want to configure the API URL (especially in production):

```py
# API_URL will be used to set the "Location" header field
# after a resource has been created (POST) as per RFC 7231
# and the "Link" header field (pagination) as per RFC 8288
API_URL = "http://localhost:8000"
```

* That's it! Now run the API and play with it live! All thanks to [FastAPI](https://github.com/tiangolo/fastapi) generating the OpenAPI specs and embedding [Swagger UI](https://github.com/swagger-api/swagger-ui) 😊

```bash
$ cd src
$ uvicorn api:app
INFO:     Started server process [12884]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

* Then go to: http://localhost:8000/docs

![image](https://user-images.githubusercontent.com/4362224/202903625-096d00f4-957e-4eed-8e35-c7489673c4be.png)

### Package only

You are free to use the core package without the API.

The steps are the exact same except you don't run the API at the end.
I did provide a [`sample.py`](https://github.com/angely-dev/freeradius-api/blob/master/src/sample.py) file:

> **Note:** the term *repository* refers to the Repository pattern. See the [#conceptual-approach](#conceptual-approach).

```py
from database import db_connect
from pyfreeradius.models import User, Group, Nas, AttributeOpValue, UserGroup
from pyfreeradius.repositories import UserRepository, GroupRepository, NasRepository

# Load the FreeRADIUS repositories
db_connection = db_connect()
user_repo = UserRepository(db_connection)
group_repo = GroupRepository(db_connection)
nas_repo = NasRepository(db_connection)

# Add some NASes
n1 = Nas(nasname="1.1.1.1", shortname="my-super-nas", secret="my-super-secret")
n2 = Nas(nasname="2.2.2.2", shortname="my-other-nas", secret="my-other-secret")
if not nas_repo.exists(n1.nasname) and not nas_repo.exists(n2.nasname):
    nas_repo.add(n1)
    nas_repo.add(n2)

# Add some groups
g1 = Group(groupname="my-super-group", replies=[AttributeOpValue(attribute="Filter-Id", op=":=", value="100m")])
g2 = Group(groupname="my-other-group", replies=[AttributeOpValue(attribute="Filter-Id", op=":=", value="200m")])
if not group_repo.exists(g1.groupname) and not group_repo.exists(g2.groupname):
    group_repo.add(g1)
    group_repo.add(g2)

# Add some users
u1 = User(
    username="my-super-user",
    groups=[UserGroup(groupname=g1.groupname)],
    checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="my-super-pass")],
    replies=[
        AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.1"),
        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24"),
        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24"),
        AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="my-super-vrf"),
    ],
)
u2 = User(
    username="my-other-user",
    checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="my-other-pass")],
    replies=[
        AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.2"),
        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.1.0/24"),
        AttributeOpValue(attribute="Framed-Route", op="+=", value="192.168.2.0/24"),
        AttributeOpValue(attribute="Huawei-Vpn-Instance", op=":=", value="my-other-vrf"),
    ],
)
if not user_repo.exists(u1.username) and not user_repo.exists(u2.username) and group_repo.exists(g1.groupname):
    user_repo.add(u1)
    user_repo.add(u2)

# Some printing
print(nas_repo.find_all_nasnames())
print(user_repo.find_all_usernames())
print(group_repo.find_all_groupnames())
print(group_repo.has_users(g1.groupname))  # will print True
print(group_repo.has_users(g2.groupname))  # will print False

# Remove what we added
nas_repo.remove(n1.nasname)
nas_repo.remove(n2.nasname)
user_repo.remove(u1.username)
user_repo.remove(u2.username)

if not group_repo.has_users(g1.groupname) and not group_repo.has_users(g2.groupname):
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

⚠️ If you use the `pyfreeradius` package directly like this, be cautious with the logic you implement over it (since none is implemented by the repositories and very little by the Pydantic models). Without any guards, this can lead to invalid states in the database (e.g., user added twice, belonging to a non-existing group). As a starting point, you may want to use the logic contained in the `sample.py` file (e.g., `exists`, `has_users`).

### Unit tests

If desired, feel free to run the unit tests to ensure your install is fully working:

```bash
/tmp/freeradius-api-master$ pip install -r requirements-dev.txt
```

```bash
/tmp/freeradius-api-master$ pytest -v --cov-report term --cov=. src/tests/
========================================= test session starts ==========================================
platform linux -- Python 3.10.12, pytest-8.3.3, pluggy-1.5.0 -- /tmp/freeradius-api-master/venv/bin/python3
cachedir: .pytest_cache
rootdir: /tmp/freeradius-api-master
configfile: pyproject.toml
plugins: cov-5.0.0, anyio-4.6.2.post1
collected 14 items

src/tests/test_api.py::test_read_root PASSED                                                     [  7%]
src/tests/test_api.py::test_nas PASSED                                                           [ 14%]
src/tests/test_api.py::test_group PASSED                                                         [ 21%]
src/tests/test_api.py::test_user PASSED                                                          [ 28%]
src/tests/test_api.py::test_delete_user_group PASSED                                             [ 35%]
src/tests/test_pyfreeradius.py::test_invalid_user PASSED                                         [ 42%]
src/tests/test_pyfreeradius.py::test_invalid_group PASSED                                        [ 50%]
src/tests/test_pyfreeradius.py::test_invalid_usergroup PASSED                                    [ 57%]
src/tests/test_pyfreeradius.py::test_invalid_nas PASSED                                          [ 64%]
src/tests/test_pyfreeradius.py::test_valid_user PASSED                                           [ 71%]
src/tests/test_pyfreeradius.py::test_valid_group PASSED                                          [ 78%]
src/tests/test_pyfreeradius.py::test_valid_nas PASSED                                            [ 85%]
src/tests/test_pyfreeradius.py::test_usergroup PASSED                                            [ 92%]
src/tests/test_pyfreeradius.py::test_groupuser PASSED                                            [100%]

---------- coverage: platform linux, python 3.10.12-final-0 ----------
Name                               Stmts   Miss  Cover
------------------------------------------------------
src/api.py                            98      0   100%
src/database.py                        5      0   100%
src/dependencies.py                   17      0   100%
src/pyfreeradius/__init__.py           0      0   100%
src/pyfreeradius/models.py            45      0   100%
src/pyfreeradius/repositories.py     190      0   100%
src/settings.py                       13      0   100%
src/tests/__init__.py                  0      0   100%
src/tests/test_api.py                 85      0   100%
src/tests/test_pyfreeradius.py        87      0   100%
------------------------------------------------------
TOTAL                                540      0   100%


========================================== 14 passed in 1.11s ==========================================
```

To generate an HTML report for checking not covered lines:

```bash
/tmp/freeradius-api-master$ pytest --cov-report html --cov=. src/tests/
```

# Keyset pagination

As of [v1.3.0](https://github.com/angely-dev/freeradius-api/tree/v1.3.0), results are paginated (fetching all results at once is generally not needed nor recommended). There are two common options for pagination:

* Offset pagination (aka `LIMIT` + `OFFSET`) — not implemented
* **Keyset pagination (aka `WHERE` + `LIMIT`) — implemented**

In the era of infinite scroll, the latter is generally preferred over the former. Not only is it better at performance but also simpler to implement.

## Using the package

Here is an example for fetching usernames (the same applies for groupnames and nasnames):

```py
# Before v1.3.0
print(user_repo.find_all_usernames())              # NOT recommended

# As of v1.3.0
print(user_repo.find_usernames())                  # fetches first usernames
print(user_repo.find_usernames(from_username='k')) # fetches usernames starting from k
```

```py
# Reminder: to check if a username exists, use the "exists" method
'aaa' in user_repo.find_all_usernames() # bad!
user_repo.exists('aaa')                 # good
```

The number of items per page is settable in the [`src/settings.py`](https://github.com/angely-dev/freeradius-api/blob/master/src/settings.py) file (it defaults to `100`).

## Using the API

Pagination is done through HTTP response headers (as per [RFC 8288](https://www.rfc-editor.org/rfc/rfc8288)) rather than JSON metadata. This is [debatable](https://news.ycombinator.com/item?id=12123511) but I prefer the returned JSON to contain only business data. Actually, this is what [GitHub API does](https://docs.github.com/en/rest/guides/using-pagination-in-the-rest-api#using-link-headers).

Here is an example for fetching usernames (the same applies for groupnames and nasnames):

```bash
$ curl -X 'GET' -i http://localhost:8000/users
HTTP/1.1 200 OK
date: Mon, 05 Jun 2023 20:07:09 GMT
server: uvicorn
content-length: 121
content-type: application/json
link: <http://localhost:8000/users?from_username=acb>; rel="next" # notice the Link header

["aaa","aab","aac","aad","aae","aaf","aag","aah","aai","aba","abb","abc","abd","abe","abf","abg","abh","abi","aca","acb"]
```

The API consumer (e.g., a frontend app) can then scroll to the next page `/users?from_username=acb`:

```bash
$ curl -X 'GET' -i http://localhost:8000/users?from_username=acb
HTTP/1.1 200 OK
date: Mon, 05 Jun 2023 20:07:43 GMT
server: uvicorn
content-length: 121
content-type: application/json
link: <http://localhost:8000/users?from_username=aed>; rel="next" # notice the Link header

["acc","acd","ace","acf","acg","ach","aci","ada","adb","adc","add","ade","adf","adg","adh","adi","aea","aeb","aec","aed"]
```

And so on until there are no more results to fetch:

```bash
$ curl -X 'GET' -i http://localhost:8000/users?from_username=zzz
HTTP/1.1 200 OK
date: Mon, 05 Jun 2023 20:08:06 GMT
server: uvicorn
content-length: 2
content-type: application/json
# no more Link header
```

> Only `rel="next"` is implemented since there wasn't a need yet for `rel="prev|last|first"`.

## SQL explanation

There are plenty of articles about keyset pagination ([here is one](https://use-the-index-luke.com/no-offset), [here is another one](https://www.cockroachlabs.com/docs/stable/pagination.html)). The idea is to fetch limited results starting from a certain key.

> In general, that key is also a `KEY` or an `INDEX` in the SQL sense, which is used to speed up the lookup. This is the case in the FreeRADIUS database schema: username, groupname and nasname are all keys.

The query template looks like:

```sql
SELECT * FROM my_table
WHERE my_key > my_value
ORDER BY my_key
LIMIT 20
```

Because in our case the lookup occurs in different tables, the query must be adapted to:

```sql
-- Keyset pagination for fetching usernames
SELECT username FROM (
        SELECT DISTINCT username FROM {RADCHECK}
  UNION SELECT DISTINCT username FROM {RADREPLY}
  UNION SELECT DISTINCT username FROM {RADUSERGROUP}
) u WHERE username > %s ORDER BY username LIMIT {PER_PAGE}
```

The issue [#1](https://github.com/angely-dev/freeradius-api/issues/1) provides more explanation about query performance and DBMSs support.

> **In particular, the above SQL query breaks compatibility with Oracle and MSSQL.** Queries must be (easily) adapted for these DBMSs. The choice is assumed, considering that MySQL and PostgreSQL are more common for FreeRADIUS. For now, I still want to avoid an ORM like SQLAlchemy.

# API authentication

You may want to add authentication to the API.

## TL;DR

A simple solution is through API key.
Only two steps are required this way:

* Create `src/auth.py`:

```py
from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader

_x_api_key = 'my-valid-key'
_x_api_key_header = APIKeyHeader(name='X-API-Key')

async def verify_key(x_api_key: str = Depends(_x_api_key_header)):
    if x_api_key != _x_api_key:
        raise HTTPException(401, 'Invalid key')
```

* Apply following changes in `src/api.py`:

```diff
# top of the file
+from auth import verify_key
+from fastapi import Depends

# bottom of the file
-app = FastAPI(title='FreeRADIUS REST API')
+app = FastAPI(title='FreeRADIUS REST API', dependencies=[Depends(verify_key)])
```

That's it! All endpoints now require authentication.

> In the above code, we make use of both [global dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/global-dependencies/) and [security](https://fastapi.tiangolo.com/tutorial/security/first-steps/) features of FastAPI. API key is not properly documented yet but the issue https://github.com/tiangolo/fastapi/issues/142 provides some working snippets.

> The key would not normally go "in the clear" in the code like this. Depending on your setup, it would be passed using CI/CD variables for example.

## Demo

### Using `curl`

```sh
$ curl -X 'GET' -i http://localhost:8000/users
HTTP/1.1 403 Forbidden

{"detail":"Not authenticated"}
```
```sh
$ curl -X 'GET' -H 'X-API-Key: an-invalid-key' -i http://localhost:8000/users
HTTP/1.1 401 Unauthorized

{"detail":"Invalid key"}
```
```sh
$ curl -X 'GET' -H 'X-API-Key: my-valid-key' -i http://localhost:8000/users
HTTP/1.1 200 OK

["bob","alice@adsl","eve","oscar@wil.de"]
```

### Using the Web UI

Because the API key security scheme is part of the [OpenAPI specification](https://swagger.io/specification/#security-scheme-object), the need for authentication gets specified on the Web UI 😊

* You will now notice an `Authorize` button at the top-right corner as well as a little lock on each endpoint:

![swagger-auth-1](https://user-images.githubusercontent.com/4362224/214641998-2f323fb2-b90a-45a6-a09b-e4eadf1d1a29.png)

* To play with the API, you first need to provide the key by clicking that `Authorize` button:

![swagger-auth-2](https://user-images.githubusercontent.com/4362224/214642029-985ea676-bfe2-468f-bad8-c105b5cc5d69.png)

* Alternatively, on the Redoc Web UI:

![redoc-auth](https://user-images.githubusercontent.com/4362224/214642067-6c461a34-2679-43e2-88a7-b6316c459ae9.png)

## Explanation

FastAPI supports multiple security schemes, including OAuth2, API key and others. OAuth2 is a vast subject and will not be treated here. API key is a simple mechanism you probably already used in some projects. The [Swagger doc](https://swagger.io/docs/specification/authentication/api-keys/) explains it very well:

> **An API key is a token that a client provides when making API calls.** The key can be sent in the query string or as a request header or as a cookie. API keys are supposed to be a secret that only the client and server know. Like Basic authentication, **API key-based authentication is only considered secure if used together with other security mechanisms such as HTTPS/SSL.**

A request header is quite common. Some examples:

* `X-API-Key: <TOKEN>` (as per the Swagger doc and the one I used in the solution)
* `X-Auth-Token: <TOKEN>` (e.g., LibreNMS)
* `Authorization: Token <TOKEN>` (e.g., NetBox and [DjangoREST-based projects](https://github.com/encode/django-rest-framework/blob/3.14.0/rest_framework/authentication.py#L151-L161) more generally)
* `Authorization: Bearer <TOKEN>` (in accordance with [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750#section-2.1) of the OAuth2 framework)

> The `X-` prefix denotes a non-standard HTTP header. You can set whatever name you prefer after that `X-`. The associated semantic is up to you. Some interesting background about the `X-` convention can be found in [RFC 6648](https://www.rfc-editor.org/rfc/rfc6648#appendix-A) which, by the way, officially deprecates it.

> Although `Authorization: Token` seems more standard as it follows [RFC 2617](https://www.rfc-editor.org/rfc/rfc2617) syntax, note the `Token` authentication scheme is not part of the [IANA HTTP Authentication Scheme Registry](https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml) so it is still custom in a sense. The only true standard header is `Authorization: Bearer` introduced by the OAuth2 framework.

# Conceptual approach

You may be interested in the model-centric approach taken (or you may not).

**The implementation is fairly easy but it is good to know it conforms to some pattern.**

## Domain-Driven Design (DDD)

I found similarities with the DDD and especially the **Repository pattern.** It is a well-known pattern, yet often poorly applied, particularly in CRUD apps where there is a one-to-one mapping between entities and the database. In that case, the Repository just adds an extra layer for nothing really. I found it well-suited here because the "raw" database schema differs from the object-oriented or the "business" view of the Domain (the subject area).

> A REPOSITORY represents all objects of a certain type as a conceptual set **(usually emulated).** It acts like a collection, except with more elaborate querying capability. Objects of the appropriate type are added and removed, and the machinery behind the REPOSITORY inserts them or deletes them from the database. **The easiest REPOSITORY to build has hard-coded queries with specific parameters.** These queries can be various: retrieving an ENTITY by its identity (…)
>
> — Domain-Driven Design: Tackling Complexity in the Heart of Software. Eric Evans

Repositories are responsible for mapping Domain Objects to the database where they get flattened in some way:

![image](https://user-images.githubusercontent.com/4362224/202743771-07877b22-da82-4967-8bd5-1e62bb2f1e9a.png)

The Domain Services (corresponding to the `api.py` file) call the repositories to implement the Domain Logic which cannot fit in the Domain Objects directly (typically, when fetching data from different repositories is required for validation purpose). As per the DDD, the Domain Objects are classified this way:

* **Entities:** they have an identity and a lifecycle interest (`User`, `Group` and `Nas`)
* **Value Objects:** they have no conceptual identity and are Entity characteristics (`AttributeOpValue`)
* **Aggregate Root:** set of Entities and Value Objects with a well-defined boundary, the root being an Entity (a repository is then designed for each Aggregate Root)

`User` and `Group` are Aggregate Roots (they both aggregate check and reply attributes). `Nas` is also an Aggregate Root (it has its own boundary). Moreover, `User` and `Group` being linked together, this will produce some kind of association-class. In such a case, it is preferable to reference aggregates "by identity" to prevent boundary crossing:

> Prefer references to external aggregates only by their globally unique identity, not by holding a direct object reference (or “pointer”).
>
> — [Effective Aggregate Design, Part II: Making Aggregates Work Together.](https://www.dddcommunity.org/library/vernon_2011/) Vaughn Vernon

## Class diagram

The UML class diagram may help to bring semantic and an object-oriented view of the FreeRADIUS database schema (therefore, this is NOT a one-to-one mapping with that schema).

![uml-class-diagram](https://user-images.githubusercontent.com/4362224/202876207-bc272618-a8d8-407d-a5fe-a523aaf492e8.png)

As represented, the `AttributeOpValue` class should be ideally subclassed since the sets of supported attributes and operators differ between the subclasses. This could be implemented with Enums. However, for simplicity, I decided not to do it, mainly because it would have meant reinventing (or integrating in some way) the RADIUS dictionaries.

Also, I limited the `Nas` attributes but you can add more if needed, .e.g., `type`, `community`, etc.

### Semantic

The diagram must be interpreted as follows:

* A `User` may have `Check` or `Reply` attributes — if the user is deleted, so are its attributes
* A `Group` may have `Check` or `Reply` attributes — if the group is deleted, so are its attributes
* A `User` may belong to multiple `Group` — if the user is deleted, so are its belonging to groups
* A `Group` may contain multiple `User` — if the group is deleted, so are its belonging to users

> To prevent accidental deletion however (when a group still contains legit users), we can think of a flag like `ignoreUsers` to be passed.

* User groups are ordered by a `priority` which semantic is fully documented in the [rlm_sql](https://wiki.freeradius.org/modules/Rlm_sql) module
* The `Nas` could be a standalone class. Alternatively, we can consider it depends on `User` as NASes perform AAA requests on them. This choice will have no consequence on the implementation as per the UML standard:

> The presence of Dependency relationships in a model does not have any runtime semantic implications.

### Some common sense (expressed by the property modifiers)

* A `username` is like an ID (two users cannot share the same one) — hence the use of `{id}`
* A `groupname` is like an ID (two groups cannot share the same one) — hence the use of `{id}`
* A `nasname` is like an ID (two NASes cannot share the same one) — hence the use of `{id}`
* A `User` cannot belong twice to the same `Group` — hence the use of `{unique}`
* A `Group` cannot contain twice to the same `User` — hence the use of `{unique}`

### Some more constraints (not graphically represented)

* A `Group` must have at least one `Check` or one `Reply` attribute
* A `User` must have at least one `Check` or one `Reply` attribute, or must belong to at least one `Group`
* Otherwise, they won't really exist in the database as per the FreeRADIUS schema

Theoretically, a `Group` may exist without any attributes but with users in it, though I don't see any practical use.
