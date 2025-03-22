from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

from dependencies import GroupRepositoryDep, NasRepositoryDep, UserRepositoryDep
from pyfreeradius.models import Group, Nas, User
from schemas import GroupUpdate, NasUpdate, UserUpdate
from settings import API_URL


# Error model and responses
class RadAPIError(BaseModel):
    detail: str


error_404 = {"model": RadAPIError, "description": "Item not found"}
error_409 = {"model": RadAPIError, "description": "Item already exists"}

# Our API router and routes
router = APIRouter()


@router.get("/")
def read_root():
    return {"Welcome!": f"API docs is available at {API_URL}/docs"}


@router.get("/nas", tags=["nas"], status_code=200, response_model=list[Nas])
def get_nases(nas_repo: NasRepositoryDep, response: Response, from_nasname: str | None = None):
    nasnames = nas_repo.find_all(from_nasname)
    if nasnames:
        last_nasname = nasnames[-1].nasname
        response.headers["Link"] = f'<{API_URL}/nas?from_nasname={last_nasname}>; rel="next"'
    return nasnames


@router.get("/users", tags=["users"], status_code=200, response_model=list[User])
def get_users(user_repo: UserRepositoryDep, response: Response, from_username: str | None = None):
    usernames = user_repo.find_all(from_username)
    if usernames:
        last_username = usernames[-1].username
        response.headers["Link"] = f'<{API_URL}/users?from_username={last_username}>; rel="next"'
    return usernames


@router.get("/groups", tags=["groups"], status_code=200, response_model=list[Group])
def get_groups(group_repo: GroupRepositoryDep, response: Response, from_groupname: str | None = None):
    groupnames = group_repo.find_all(from_groupname)
    if groupnames:
        last_groupname = groupnames[-1].groupname
        response.headers["Link"] = f'<{API_URL}/groups?from_groupname={last_groupname}>; rel="next"'
    return groupnames


@router.get("/nas/{nasname}", tags=["nas"], status_code=200, response_model=Nas, responses={404: error_404})
def get_nas(nasname: str, nas_repo: NasRepositoryDep):
    nas = nas_repo.find_one(nasname)
    if not nas:
        raise HTTPException(404, "Given NAS does not exist")
    return nas


@router.get("/users/{username}", tags=["users"], status_code=200, response_model=User, responses={404: error_404})
def get_user(username: str, user_repo: UserRepositoryDep):
    user = user_repo.find_one(username)
    if not user:
        raise HTTPException(404, "Given user does not exist")
    return user


@router.get("/groups/{groupname}", tags=["groups"], status_code=200, response_model=Group, responses={404: error_404})
def get_group(groupname: str, group_repo: GroupRepositoryDep):
    group = group_repo.find_one(groupname)
    if not group:
        raise HTTPException(404, "Given group does not exist")
    return group


@router.post("/nas", tags=["nas"], status_code=201, response_model=Nas, responses={409: error_409})
def post_nas(nas: Nas, nas_repo: NasRepositoryDep, response: Response):
    if nas_repo.exists(nas.nasname):
        raise HTTPException(409, "Given NAS already exists")

    nas_repo.add(nas)
    response.headers["Location"] = f"{API_URL}/nas/{nas.nasname}"
    return nas


@router.post("/users", tags=["users"], status_code=201, response_model=User, responses={409: error_409})
def post_user(
    user: User,
    user_repo: UserRepositoryDep,
    group_repo: GroupRepositoryDep,
    response: Response,
    allow_groups_creation: Annotated[
        bool, Query(description="If set to true, nonexistent groups will be created during user creation")
    ] = False,
):
    if user_repo.exists(user.username):
        raise HTTPException(409, "Given user already exists")

    if not allow_groups_creation:
        for usergroup in user.groups:
            if not group_repo.exists(usergroup.groupname):
                raise HTTPException(
                    422,
                    (
                        f"Given group '{usergroup.groupname}' does not exist: "
                        "create it first or set 'allow_groups_creation' parameter to true"
                    ),
                )

    user_repo.add(user)
    response.headers["Location"] = f"{API_URL}/users/{user.username}"
    return user


@router.post("/groups", tags=["groups"], status_code=201, response_model=Group, responses={409: error_409})
def post_group(
    group: Group,
    group_repo: GroupRepositoryDep,
    user_repo: UserRepositoryDep,
    response: Response,
    allow_users_creation: Annotated[
        bool, Query(description="If set to true, nonexistent users will be created during group creation")
    ] = False,
):
    if group_repo.exists(group.groupname):
        raise HTTPException(409, "Given group already exists")

    if not allow_users_creation:
        for groupuser in group.users:
            if not user_repo.exists(groupuser.username):
                raise HTTPException(
                    422,
                    (
                        f"Given user '{groupuser.username}' does not exist: "
                        "create it first or set 'allow_users_creation' parameter to true"
                    ),
                )

    group_repo.add(group)
    response.headers["Location"] = f"{API_URL}/groups/{group.groupname}"
    return group


@router.delete("/nas/{nasname}", tags=["nas"], status_code=204, responses={404: error_404})
def delete_nas(nasname: str, nas_repo: NasRepositoryDep):
    if not nas_repo.exists(nasname):
        raise HTTPException(404, "Given NAS does not exist")

    nas_repo.remove(nasname)


@router.delete("/users/{username}", tags=["users"], status_code=204, responses={404: error_404})
def delete_user(
    username: str,
    user_repo: UserRepositoryDep,
    group_repo: GroupRepositoryDep,
    prevent_groups_deletion: Annotated[
        bool, Query(description="If set to false, user groups without any attributes will be deleted")
    ] = True,
):
    user = user_repo.find_one(username)
    if not user:
        raise HTTPException(404, detail="Given user does not exist")

    if prevent_groups_deletion:
        for usergroup in user.groups:
            group = group_repo.find_one(usergroup.groupname)
            if group and not (group.checks or group.replies):
                raise HTTPException(
                    422,
                    (
                        f"Group '{group.groupname}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_groups_deletion' parameter to false"
                    ),
                )

    user_repo.remove(username)


@router.delete("/groups/{groupname}", tags=["groups"], status_code=204, responses={404: error_404})
def delete_group(
    groupname: str,
    group_repo: GroupRepositoryDep,
    user_repo: UserRepositoryDep,
    ignore_users: Annotated[
        bool, Query(description="If set to true, the group will be deleted even if it still has users")
    ] = False,
    prevent_users_deletion: Annotated[
        bool, Query(description="If set to false, group users without any attributes will be deleted")
    ] = True,
):
    group = group_repo.find_one(groupname)
    if not group:
        raise HTTPException(404, "Given group does not exist")

    if group.users and not ignore_users:
        raise HTTPException(422, "Given group has users: delete them first or set 'ignore_users' parameter to true")

    if prevent_users_deletion:
        for groupuser in group.users:
            user = user_repo.find_one(groupuser.username)
            if user and not (user.checks or user.replies):
                raise HTTPException(
                    422,
                    (
                        f"User '{user.username}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_users_deletion' parameter to false"
                    ),
                )

    group_repo.remove(groupname)


@router.patch("/nas/{nasname}", tags=["nas"], status_code=200, response_model=Nas, responses={404: error_404})
def patch_nas(
    nasname: str,
    nas_update: NasUpdate,
    nas_repo: NasRepositoryDep,
    response: Response,
):
    nas = nas_repo.find_one(nasname)
    if not nas:
        raise HTTPException(404, "Given NAS does not exist")

    nas_repo.set(nasname, new_shortname=nas_update.shortname, new_secret=nas_update.secret)
    response.headers["Location"] = f"{API_URL}/nas/{nasname}"
    return nas_repo.find_one(nasname)


@router.patch("/users/{username}", tags=["users"], status_code=200, response_model=User, responses={404: error_404})
def patch_user(
    username: str,
    user_update: UserUpdate,
    user_repo: UserRepositoryDep,
    group_repo: GroupRepositoryDep,
    response: Response,
    prevent_groups_deletion: Annotated[
        bool, Query(description="If set to false, user groups without any attributes will be deleted")
    ] = True,
):
    user = user_repo.find_one(username)
    if not user:
        raise HTTPException(404, "Given user does not exist")

    if user_update.groups:
        for usergroup in user_update.groups:
            if not group_repo.exists(usergroup.groupname):
                raise HTTPException(422, f"Given group '{usergroup.groupname}' does not exist: create it first")

    if (user_update.groups or user_update.groups == []) and prevent_groups_deletion:
        for usergroup in user.groups:
            group = group_repo.find_one(usergroup.groupname)
            if group and not (group.checks or group.replies):
                raise HTTPException(
                    422,
                    (
                        f"Group '{group.groupname}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_groups_deletion' parameter to false"
                    ),
                )

    new_checks = user.checks if user_update.checks is None else user_update.checks
    new_replies = user.replies if user_update.replies is None else user_update.replies
    new_groups = user.groups if user_update.groups is None else user_update.groups
    if not (new_checks or new_replies or new_groups):
        raise HTTPException(422, "Resulting user would have no attributes and no groups")

    user_repo.set(
        username, new_checks=user_update.checks, new_replies=user_update.replies, new_groups=user_update.groups
    )
    response.headers["Location"] = f"{API_URL}/users/{username}"
    return user_repo.find_one(username)


@router.patch("/groups/{groupname}", tags=["groups"], status_code=200, response_model=Group, responses={404: error_404})
def patch_group(
    groupname: str,
    group_update: GroupUpdate,
    group_repo: GroupRepositoryDep,
    user_repo: UserRepositoryDep,
    response: Response,
    prevent_users_deletion: Annotated[
        bool, Query(description="If set to false, group users without any attributes will be deleted")
    ] = True,
):
    group = group_repo.find_one(groupname)
    if not group:
        raise HTTPException(404, "Given group does not exist")

    if (group_update.users or group_update.users == []) and prevent_users_deletion:
        for groupuser in group.users:
            user = user_repo.find_one(groupuser.username)
            if user and not (user.checks or user.replies):
                raise HTTPException(
                    422,
                    (
                        f"User '{user.username}' would be deleted as it has no attributes: "
                        "delete it first or set 'prevent_users_deletion' parameter to false"
                    ),
                )

    if group_update.users:
        for groupuser in group_update.users:
            if not user_repo.exists(groupuser.username):
                raise HTTPException(422, f"Given user '{groupuser.username}' does not exist: create it first")

    new_checks = group.checks if group_update.checks is None else group_update.checks
    new_replies = group.replies if group_update.replies is None else group_update.replies
    new_users = group.users if group_update.users is None else group_update.users
    if not (new_checks or new_replies or new_users):
        raise HTTPException(422, "Resulting group would have no attributes and no users")

    group_repo.set(
        groupname, new_checks=group_update.checks, new_replies=group_update.replies, new_users=group_update.users
    )
    response.headers["Location"] = f"{API_URL}/groups/{groupname}"
    return group_repo.find_one(groupname)


# API is now ready!
app = FastAPI(title="FreeRADIUS REST API")
app.include_router(router)
