from api import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test data

post_group = {"groupname": "g", "replies": [{"attribute": "Filter-Id", "op": ":=", "value": "10m"}]}

post_group_bad_user = post_group | {"users": [{"username": "non-existing-user", "priority": 1}]}

post_user = {
    "username": "u",
    "checks": [{"attribute": "Cleartext-Password", "op": ":=", "value": "my-pass"}],
    "replies": [
        {"attribute": "Framed-IP-Address", "op": ":=", "value": "10.0.0.1"},
        {"attribute": "Framed-Route", "op": "+=", "value": "192.168.1.0/24"},
        {"attribute": "Framed-Route", "op": "+=", "value": "192.168.2.0/24"},
        {"attribute": "Huawei-Vpn-Instance", "op": ":=", "value": "my-vrf"},
    ],
}

post_user_bad_group = post_user | {"groups": [{"groupname": "non-existing-group", "priority": 1}]}

post_user_with_group = post_user | {"groups": [{"groupname": "g", "priority": 1}]}

post_nas = {"nasname": "5.5.5.5", "secret": "my-secret", "shortname": "my-nas"}

# Expected results

get_group = {
    "groupname": "g",
    "checks": [],
    "replies": [{"attribute": "Filter-Id", "op": ":=", "value": "10m"}],
    "users": [],
}

get_user = {
    "username": "u",
    "checks": [{"attribute": "Cleartext-Password", "op": ":=", "value": "my-pass"}],
    "replies": [
        {"attribute": "Framed-IP-Address", "op": ":=", "value": "10.0.0.1"},
        {"attribute": "Framed-Route", "op": "+=", "value": "192.168.1.0/24"},
        {"attribute": "Framed-Route", "op": "+=", "value": "192.168.2.0/24"},
        {"attribute": "Huawei-Vpn-Instance", "op": ":=", "value": "my-vrf"},
    ],
    "groups": [{"groupname": "g", "priority": 1}],
}

get_nas = {"nasname": "5.5.5.5", "secret": "my-secret", "shortname": "my-nas"}

# Tests


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


def test_nas():
    response = client.get("/nas/5.5.5.5")
    assert response.status_code == 404  # NAS not found yet

    response = client.get("/nas")
    assert response.status_code == 200
    assert "5.5.5.5" not in response.json()  # NAS not part of collection yet

    response = client.post("/nas", json=post_nas)
    assert response.status_code == 201  # NAS created
    assert response.json() == get_nas

    response = client.post("/nas", json=post_nas)
    assert response.status_code == 409  # NAS already exists

    response = client.get("/nas/5.5.5.5")
    assert response.status_code == 200  # NAS now found
    assert response.json() == get_nas

    response = client.get("/nas")
    assert response.status_code == 200
    assert "5.5.5.5" in response.json()  # NAS now part of collection

    response = client.delete("/nas/5.5.5.5")
    assert response.status_code == 204  # NAS deleted

    response = client.delete("/nas/5.5.5.5")
    assert response.status_code == 404  # NAS now not found


def test_group():
    response = client.get("/groups/g")
    assert response.status_code == 404  # group not found yet

    response = client.get("/groups")
    assert response.status_code == 200
    assert "g" not in response.json()  # group not part of collection yet

    response = client.post("/groups", json=post_group_bad_user)
    assert response.status_code == 422  # user does not exist

    response = client.post("/groups", json=post_group)
    assert response.status_code == 201  # group created
    assert response.json() == get_group

    response = client.post("/groups", json=post_group)
    assert response.status_code == 409  # group already exists

    response = client.get("/groups/g")
    assert response.status_code == 200  # group now found
    assert response.json() == get_group

    response = client.get("/groups")
    assert response.status_code == 200
    assert "g" in response.json()  # group now part of collection


def test_user():
    response = client.get("/users/u")
    assert response.status_code == 404  # user not found yet

    response = client.get("/users")
    assert response.status_code == 200
    assert "u" not in response.json()  # user not part of collection yet

    response = client.post("/users", json=post_user_bad_group)
    assert response.status_code == 422  # group does not exist

    response = client.post("/users", json=post_user_with_group)
    assert response.status_code == 201  # user created
    assert response.json() == get_user

    response = client.post("/users", json=post_user_with_group)
    assert response.status_code == 409  # user already exists

    response = client.get("/users/u")
    assert response.status_code == 200  # user now found
    assert response.json() == get_user

    response = client.get("/users")
    assert response.status_code == 200
    assert "u" in response.json()  # user now part of collection


def test_delete_user_group():
    response = client.delete("/groups/g")
    assert response.status_code == 422  # group still has users

    response = client.delete("/users/u")
    assert response.status_code == 204  # user deleted

    response = client.delete("/users/u")
    assert response.status_code == 404  # user now not found

    response = client.delete("/groups/g")
    assert response.status_code == 204  # group deleted

    response = client.delete("/groups/g")
    assert response.status_code == 404  # group now not found
