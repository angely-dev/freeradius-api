import pytest
from pydantic import ValidationError

from src.pyfreeradius import (
    AttributeOpValue,
    User,
    UserGroup,
    UserUpdate,
    Group,
    GroupUpdate,
    Nas,
    NasUpdate
)


def test_attribute_op_value_validation():
    """Test AttributeOpValue model validation"""
    # Valid attribute
    attr = AttributeOpValue(attribute="Cleartext-Password", op=":=", value="pass")
    assert attr.attribute == "Cleartext-Password"
    assert attr.op == ":="
    assert attr.value == "pass"

    # Invalid: empty attribute
    with pytest.raises(ValidationError):
        AttributeOpValue(attribute="", op=":=", value="pass")

    # Invalid: empty op
    with pytest.raises(ValidationError):
        AttributeOpValue(attribute="Cleartext-Password", op="", value="pass")

    # Invalid: empty value
    with pytest.raises(ValidationError):
        AttributeOpValue(attribute="Cleartext-Password", op=":=", value="")


def test_user_group_validation():
    """Test UserGroup model validation"""
    # Valid user group
    ug = UserGroup(groupname="test-group", priority=10)
    assert ug.groupname == "test-group"
    assert ug.priority == 10

    # Valid with default priority
    ug = UserGroup(groupname="test-group")
    assert ug.priority == 1

    # Invalid: empty groupname
    with pytest.raises(ValidationError):
        UserGroup(groupname="")


def test_user_validation():
    """Test User model validation"""
    # Valid user with checks
    user = User(
        username="test-user",
        checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="pass")]
    )
    assert user.username == "test-user"
    assert len(user.checks) == 1

    # Valid user with replies
    user = User(
        username="test-user",
        replies=[AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.1")]
    )
    assert user.username == "test-user"
    assert len(user.replies) == 1

    # Valid user with groups
    user = User(
        username="test-user",
        groups=[UserGroup(groupname="test-group")]
    )
    assert user.username == "test-user"
    assert len(user.groups) == 1

    # Invalid: user with no attributes
    with pytest.raises(ValueError, match="User must have at least one check or one reply attribute"):
        User(username="test-user")

    # Invalid: duplicate groups
    with pytest.raises(ValueError, match="Given groups have one or more duplicates"):
        User(
            username="test-user",
            checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="pass")],
            groups=[UserGroup(groupname="group1"), UserGroup(groupname="group1")]
        )


def test_user_update_validation():
    """Test UserUpdate model validation"""
    # Valid update with checks
    update = UserUpdate(
        checks=[AttributeOpValue(attribute="Cleartext-Password", op=":=", value="new-pass")]
    )
    assert len(update.checks) == 1

    # Valid update with replies
    update = UserUpdate(
        replies=[AttributeOpValue(attribute="Framed-IP-Address", op=":=", value="10.0.0.2")]
    )
    assert len(update.replies) == 1

    # Valid update with groups
    update = UserUpdate(groups=[UserGroup(groupname="new-group")])
    assert len(update.groups) == 1

    # Invalid: update with no attributes
    with pytest.raises(ValueError, match="Request must have at least one check, one reply attribute or one group"):
        UserUpdate()

    # Invalid: duplicate groups
    with pytest.raises(ValueError, match="Given groups have one or more duplicates"):
        UserUpdate(
            groups=[UserGroup(groupname="group1"), UserGroup(groupname="group1")]
        )


def test_group_validation():
    """Test Group model validation"""
    # Valid group with checks
    group = Group(
        groupname="test-group",
        checks=[AttributeOpValue(attribute="Auth-Type", op=":=", value="Accept")]
    )
    assert group.groupname == "test-group"
    assert len(group.checks) == 1

    # Valid group with replies
    group = Group(
        groupname="test-group",
        replies=[AttributeOpValue(attribute="Filter-Id", op=":=", value="100m")]
    )
    assert group.groupname == "test-group"
    assert len(group.replies) == 1

    # Invalid: group with no attributes
    with pytest.raises(ValueError, match="Group must have at least one check or one reply attribute"):
        Group(groupname="test-group")


def test_group_update_validation():
    """Test GroupUpdate model validation"""
    # Valid update with checks
    update = GroupUpdate(
        checks=[AttributeOpValue(attribute="Auth-Type", op=":=", value="Accept")]
    )
    assert len(update.checks) == 1

    # Valid update with replies
    update = GroupUpdate(
        replies=[AttributeOpValue(attribute="Filter-Id", op=":=", value="200m")]
    )
    assert len(update.replies) == 1

    # Invalid: update with no attributes
    with pytest.raises(ValueError, match="Request must have at least one check or one reply attribute"):
        GroupUpdate()


def test_nas_validation():
    """Test Nas model validation"""
    # Valid NAS
    nas = Nas(
        nasname="192.168.1.1",
        shortname="test-nas",
        secret="test-secret"
    )
    assert nas.nasname == "192.168.1.1"
    assert nas.shortname == "test-nas"
    assert nas.secret == "test-secret"
    assert nas.type == "other"  # default
    assert nas.ports == 0  # default

    # Invalid: empty nasname
    with pytest.raises(ValidationError):
        Nas(nasname="", secret="test-secret")

    # Invalid: empty secret
    with pytest.raises(ValidationError):
        Nas(nasname="192.168.1.1", secret="")


def test_nas_update_validation():
    """Test NasUpdate model validation"""
    # Valid update
    update = NasUpdate(shortname="new-nas", secret="new-secret")
    assert update.shortname == "new-nas"
    assert update.secret == "new-secret"

    # Valid update with only ports
    update = NasUpdate(ports=10)
    assert update.ports == 10