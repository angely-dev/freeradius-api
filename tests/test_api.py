from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)

# Test data

post_group = {"groupname": "g", "replies": [{"attribute": "Filter-Id", "op": ":=", "value": "10m"}]}

post_user = {
    "username": "u",
    "checks": [{"attribute": "Cleartext-Password", "op": ":=", "value": "my-pass"}],
    "replies": [
        {"attribute": "Framed-IP-Address", "op": ":=", "value": "10.0.0.1"},
        {"attribute": "Framed-Route", "op": "+=", "value": "192.168.1.0/24"},
        {"attribute": "Framed-Route", "op": "+=", "value": "192.168.2.0/24"},
        {"attribute": "Huawei-Vpn-Instance", "op": ":=", "value": "my-vrf"},
    ],
    "groups": []
}

post_user_with_group = {
    "username": "u",
    "checks": [{"attribute": "Cleartext-Password", "op": ":=", "value": "my-pass"}],
    "replies": [
        {"attribute": "Framed-IP-Address", "op": ":=", "value": "10.0.0.1"},
        {"attribute": "Framed-Route", "op": "+=", "value": "192.168.1.0/24"},
        {"attribute": "Framed-Route", "op": "+=", "value": "192.168.2.0/24"},
        {"attribute": "Huawei-Vpn-Instance", "op": ":=", "value": "my-vrf"},
    ],
    "groups": [{"groupname": "g", "priority": 1}]
}

post_nas = {"nasname": "5.5.5.5", "secret": "my-secret", "shortname": "my-nas"}

patch_nas = {"secret": "new-secret", "shortname": "new-nas"}

# Expected results

get_group = {
    "groupname": "g",
    "checks": [],
    "replies": [{"attribute": "Filter-Id", "op": ":=", "value": "10m"}],
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
    "groups": []
}

get_nas = {"nasname": "5.5.5.5", "secret": "my-secret", "shortname": "my-nas", "type": "other", "ports": 0, "server": "", "community": "", "description": ""}

get_nas_patched = {"nasname": "5.5.5.5", "secret": "new-secret", "shortname": "new-nas", "type": "other", "ports": 0, "server": "", "community": "", "description": ""}

# Tests


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


def test_nas():
    # Clean up any existing data
    client.delete("/nas/5.5.5.5")
    
    response = client.get("/nas/5.5.5.5")
    assert response.status_code == 404  # NAS not found yet

    response = client.get("/nas")
    assert response.status_code == 200

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

    response = client.patch("/nas/5.5.5.5", json=patch_nas)
    assert response.status_code == 200
    assert response.json() == get_nas_patched

    response = client.delete("/nas/5.5.5.5")
    assert response.status_code == 204  # NAS deleted

    response = client.delete("/nas/5.5.5.5")
    assert response.status_code == 404  # NAS now not found


def test_group():
    # Clean up any existing data
    client.delete("/groups/g")
    client.delete("/users/u")
    
    response = client.get("/groups/g")
    assert response.status_code == 404  # group not found yet

    response = client.get("/groups")
    assert response.status_code == 200

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

    # Update group with new replies
    patch_group = {"replies": [{"attribute": "Filter-Id", "op": ":=", "value": "20m"}]}
    response = client.patch("/groups/g", json=patch_group)
    assert response.status_code == 200

    response = client.delete("/groups/g")
    assert response.status_code == 204  # group deleted


def test_user():
    # Clean up any existing data
    client.delete("/users/u")
    client.delete("/groups/g")
    
    response = client.get("/users/u")
    assert response.status_code == 404  # user not found yet

    response = client.get("/users")
    assert response.status_code == 200

    response = client.post("/users", json=post_user)
    assert response.status_code == 201  # user created
    assert response.json() == get_user

    response = client.post("/users", json=post_user)
    assert response.status_code == 409  # user already exists

    response = client.get("/users/u")
    assert response.status_code == 200  # user now found
    assert response.json() == get_user

    response = client.get("/users")
    assert response.status_code == 200

    # Update user with new checks
    patch_user = {"checks": [{"attribute": "Auth-Type", "op": ":=", "value": "Accept"}]}
    response = client.patch("/users/u", json=patch_user)
    assert response.status_code == 200

    response = client.delete("/users/u")
    assert response.status_code == 204  # user deleted