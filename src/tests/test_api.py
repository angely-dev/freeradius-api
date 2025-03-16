from fastapi.testclient import TestClient

from api import app

client = TestClient(app)

# Test data

post_group = {"groupname": "g", "replies": [{"attribute": "Filter-Id", "op": ":=", "value": "10m"}]}

post_group_bad_user = post_group | {"users": [{"username": "non-existing-user", "priority": 1}]}

patch_group_only_checks = {"replies": [], "checks": [{"attribute": "Auth-Type", "op": ":=", "value": "Accept"}]}
patch_group_only_replies = {"replies": [{"attribute": "Filter-Id", "op": ":=", "value": "20m"}], "checks": []}
patch_group_bad_user = patch_group_only_checks | {"users": [{"username": "non-existing-user"}]}
patch_group_dup_user = patch_group_only_checks | {"users": [{"username": "u"}, {"username": "u"}]}

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

patch_user_only_checks = {
    "replies": [],
    "checks": [{"attribute": "Auth-Type", "op": ":=", "value": "Accept"}],
    "groups": [],
}
patch_user_only_replies = {
    "replies": [{"attribute": "Framed-IP-Address", "op": ":=", "value": "10.0.0.1"}],
    "checks": [],
    "groups": None,  # same as empty list
}
patch_user_only_groups = {
    "replies": None,  # same as empty list
    "checks": None,  # same as empty list
    "groups": [{"groupname": "g"}],
}
patch_user_bad_group = {"groups": [{"groupname": "non-existing-group"}]}
patch_user_dup_group = {"groups": [{"groupname": "g"}, {"groupname": "g"}]}

post_nas = {"nasname": "5.5.5.5", "secret": "my-secret", "shortname": "my-nas"}

patch_nas = {"secret": "new-secret", "shortname": "new-nas"}

# Expected results

get_group = {
    "groupname": "g",
    "checks": [],
    "replies": [{"attribute": "Filter-Id", "op": ":=", "value": "10m"}],
    "users": [],
}

get_group_patched_only_checks = {
    "groupname": "g",
    "checks": [{"attribute": "Auth-Type", "op": ":=", "value": "Accept"}],
    "replies": [],
    "users": [],
}

get_group_patched_only_replies = {
    "groupname": "g",
    "checks": [],
    "replies": [{"attribute": "Filter-Id", "op": ":=", "value": "20m"}],
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

get_user_patched_only_checks = {
    "username": "u",
    "checks": [{"attribute": "Auth-Type", "op": ":=", "value": "Accept"}],
    "replies": [],
    "groups": [],
}

get_user_patched_only_replies = {
    "username": "u",
    "checks": [],
    "replies": [{"attribute": "Framed-IP-Address", "op": ":=", "value": "10.0.0.1"}],
    "groups": [],
}

get_user_patched_only_groups = {
    "username": "u",
    "checks": [],
    "replies": [],
    "groups": [{"groupname": "g", "priority": 1}],
}

get_nas = {"nasname": "5.5.5.5", "secret": "my-secret", "shortname": "my-nas"}

get_nas_patched = {"nasname": "5.5.5.5", "secret": "new-secret", "shortname": "new-nas"}

# Tests


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


def test_nas():
    response = client.get("/nas/5.5.5.5")
    assert response.status_code == 404  # NAS not found yet

    response = client.get("/nas")
    assert response.status_code == 200
    assert get_nas not in response.json()  # NAS not part of collection yet

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
    assert get_nas in response.json()  # NAS now part of collection

    response = client.patch("/nas/non-existing-nas", json={})
    assert response.status_code == 404

    response = client.patch("/nas/5.5.5.5", json=patch_nas)
    assert response.status_code == 200
    assert response.json() == get_nas_patched

    response = client.delete("/nas/5.5.5.5")
    assert response.status_code == 204  # NAS deleted

    response = client.delete("/nas/5.5.5.5")
    assert response.status_code == 404  # NAS now not found


def test_group():
    response = client.get("/groups/g")
    assert response.status_code == 404  # group not found yet

    response = client.get("/groups")
    assert response.status_code == 200
    assert get_group not in response.json()  # group not part of collection yet

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
    assert get_group in response.json()  # group now part of collection

    # patch operation

    response = client.patch("/groups/non-existing-group", json={})
    assert response.status_code == 404  # group not found

    response = client.patch("/groups/g", json=patch_group_bad_user)
    assert response.status_code == 422  # user does not exist

    response = client.patch("/groups/g", json=patch_group_dup_user)
    assert response.status_code == 422  # given users have one or more duplicates

    response = client.patch("/groups/g", json={"checks": [], "replies": []})
    assert response.status_code == 422  # resulting group would have no attributes

    patch_group_only_checks["replies"] = []
    response = client.patch("/groups/g", json=patch_group_only_checks)
    assert response.status_code == 200
    assert response.json() == get_group_patched_only_checks

    response = client.patch("/groups/g", json={"checks": []})
    assert response.status_code == 422  # resulting group would have no attributes

    patch_group_only_replies["checks"] = []
    response = client.patch("/groups/g", json=patch_group_only_replies)
    assert response.status_code == 200
    assert response.json() == get_group_patched_only_replies

    response = client.patch("/groups/g", json={"replies": []})
    assert response.status_code == 422  # resulting group would have no attributes

    patch_group_only_checks["replies"] = None  # same as empty list
    response = client.patch("/groups/g", json=patch_group_only_checks)
    assert response.status_code == 200
    assert response.json() == get_group_patched_only_checks

    patch_group_only_replies["checks"] = None  # same as empty list
    response = client.patch("/groups/g", json=patch_group_only_replies)
    assert response.status_code == 200
    assert response.json() == get_group_patched_only_replies

    patch_group_only_replies["users"] = None  # same as empty list
    response = client.patch("/groups/g", json=patch_group_only_replies)
    assert response.status_code == 200
    assert response.json() == get_group_patched_only_replies


def test_user():
    response = client.get("/users/u")
    assert response.status_code == 404  # user not found yet

    response = client.get("/users")
    assert response.status_code == 200
    assert get_user not in response.json()  # user not part of collection yet

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
    assert get_user in response.json()  # user now part of collection

    # patch operation

    response = client.patch("/users/non-existing-user", json={})
    assert response.status_code == 404  # user not found

    response = client.patch("/users/u", json=patch_user_bad_group)
    assert response.status_code == 422  # group does not exist

    response = client.patch("/users/u", json=patch_user_dup_group)
    assert response.status_code == 422  # given groups have one or more duplicates

    response = client.patch("/users/u", json={"replies": [], "checks": [], "groups": []})
    assert response.status_code == 422  # resulting user would have no attributes

    response = client.patch("/users/u", json=patch_user_only_checks)
    assert response.status_code == 200
    assert response.json() == get_user_patched_only_checks

    response = client.patch("/users/u", json={"checks": []})
    assert response.status_code == 422  # resulting user would have no attributes and no groups

    response = client.patch("/users/u", json=patch_user_only_replies)
    assert response.status_code == 200
    assert response.json() == get_user_patched_only_replies

    response = client.patch("/users/u", json={"replies": []})
    assert response.status_code == 422  # resulting user would have no attributes and no groups

    response = client.patch("/users/u", json=patch_user_only_groups)
    assert response.status_code == 200
    assert response.json() == get_user_patched_only_groups

    response = client.patch("/users/u", json={"groups": []})
    assert response.status_code == 422  # resulting user would have no attributes and no groups


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
