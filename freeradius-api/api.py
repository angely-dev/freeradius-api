from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

from dependencies import GroupServiceDep, NasServiceDep, UserServiceDep
from pyfreeradius.models import Group, Nas, User
from pyfreeradius.schemas import GroupUpdate, NasUpdate, UserUpdate
from pyfreeradius.services import ServiceExceptions
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
def get_nases(nas_service: NasServiceDep, response: Response, from_nasname: str | None = None):
    nas = nas_service.get_all(from_nasname)
    if nas:
        last_nasname = nas[-1].nasname
        response.headers["Link"] = f'<{API_URL}/nas?from_nasname={last_nasname}>; rel="next"'
    return nas


@router.get("/users", tags=["users"], status_code=200, response_model=list[User])
def get_users(user_service: UserServiceDep, response: Response, from_username: str | None = None):
    users = user_service.get_all(from_username)
    if users:
        last_username = users[-1].username
        response.headers["Link"] = f'<{API_URL}/users?from_username={last_username}>; rel="next"'
    return users


@router.get("/groups", tags=["groups"], status_code=200, response_model=list[Group])
def get_groups(group_service: GroupServiceDep, response: Response, from_groupname: str | None = None):
    groups = group_service.get_all(from_groupname)
    if groups:
        last_groupname = groups[-1].groupname
        response.headers["Link"] = f'<{API_URL}/groups?from_groupname={last_groupname}>; rel="next"'
    return groups


@router.get("/nas/{nasname}", tags=["nas"], status_code=200, response_model=Nas, responses={404: error_404})
def get_nas(nasname: str, nas_service: NasServiceDep):
    try:
        return nas_service.get(nasname)
    except ServiceExceptions.NasNotFound as exc:
        raise HTTPException(404, str(exc))


@router.get("/users/{username}", tags=["users"], status_code=200, response_model=User, responses={404: error_404})
def get_user(username: str, user_service: UserServiceDep):
    try:
        return user_service.get(username)
    except ServiceExceptions.UserNotFound as exc:
        raise HTTPException(404, str(exc))


@router.get("/groups/{groupname}", tags=["groups"], status_code=200, response_model=Group, responses={404: error_404})
def get_group(groupname: str, group_service: GroupServiceDep):
    try:
        return group_service.get(groupname)
    except ServiceExceptions.GroupNotFound as exc:
        raise HTTPException(404, str(exc))


@router.post("/nas", tags=["nas"], status_code=201, response_model=Nas, responses={409: error_409})
def post_nas(nas: Nas, nas_service: NasServiceDep, response: Response):
    try:
        nas_service.create(nas)
    except ServiceExceptions.NasAlreadyExists as exc:
        raise HTTPException(409, str(exc))

    response.headers["Location"] = f"{API_URL}/nas/{nas.nasname}"
    return nas


@router.post("/users", tags=["users"], status_code=201, response_model=User, responses={409: error_409})
def post_user(
    user: User,
    user_service: UserServiceDep,
    response: Response,
    allow_groups_creation: Annotated[
        bool, Query(description="If set to true, nonexistent groups will be created during user creation")
    ] = False,
):
    try:
        user_service.create(user=user, allow_groups_creation=allow_groups_creation)
    except ServiceExceptions.UserAlreadyExists as exc:
        raise HTTPException(409, str(exc))
    except ServiceExceptions.GroupNotFound as exc:
        raise HTTPException(422, str(exc))

    response.headers["Location"] = f"{API_URL}/users/{user.username}"
    return user


@router.post("/groups", tags=["groups"], status_code=201, response_model=Group, responses={409: error_409})
def post_group(
    group: Group,
    group_service: GroupServiceDep,
    response: Response,
    allow_users_creation: Annotated[
        bool, Query(description="If set to true, nonexistent users will be created during group creation")
    ] = False,
):
    try:
        group_service.create(group=group, allow_users_creation=allow_users_creation)
    except ServiceExceptions.GroupAlreadyExists as exc:
        raise HTTPException(409, str(exc))
    except ServiceExceptions.UserNotFound as exc:
        raise HTTPException(422, str(exc))

    response.headers["Location"] = f"{API_URL}/groups/{group.groupname}"
    return group


@router.delete("/nas/{nasname}", tags=["nas"], status_code=204, responses={404: error_404})
def delete_nas(nasname: str, nas_service: NasServiceDep):
    try:
        nas_service.delete(nasname)
    except ServiceExceptions.NasNotFound as exc:
        raise HTTPException(404, str(exc))


@router.delete("/users/{username}", tags=["users"], status_code=204, responses={404: error_404})
def delete_user(
    username: str,
    user_service: UserServiceDep,
    prevent_groups_deletion: Annotated[
        bool, Query(description="If set to false, user groups without any attributes will be deleted")
    ] = True,
):
    try:
        user_service.delete(username=username, prevent_groups_deletion=prevent_groups_deletion)
    except ServiceExceptions.UserNotFound as exc:
        raise HTTPException(404, str(exc))
    except ServiceExceptions.GroupWouldBeDeleted as exc:
        raise HTTPException(422, str(exc))


@router.delete("/groups/{groupname}", tags=["groups"], status_code=204, responses={404: error_404})
def delete_group(
    groupname: str,
    group_service: GroupServiceDep,
    ignore_users: Annotated[
        bool, Query(description="If set to true, the group will be deleted even if it still has users")
    ] = False,
    prevent_users_deletion: Annotated[
        bool, Query(description="If set to false, group users without any attributes will be deleted")
    ] = True,
):
    try:
        group_service.delete(
            groupname=groupname, ignore_users=ignore_users, prevent_users_deletion=prevent_users_deletion
        )
    except ServiceExceptions.GroupNotFound as exc:
        raise HTTPException(404, str(exc))
    except (ServiceExceptions.GroupStillHasUsers, ServiceExceptions.UserWouldBeDeleted) as exc:
        raise HTTPException(422, str(exc))


@router.patch("/nas/{nasname}", tags=["nas"], status_code=200, response_model=Nas, responses={404: error_404})
def patch_nas(nasname: str, nas_update: NasUpdate, nas_service: NasServiceDep, response: Response):
    try:
        updated_nas = nas_service.update(nasname=nasname, nas_update=nas_update)
    except ServiceExceptions.NasNotFound as exc:
        raise HTTPException(404, str(exc))

    response.headers["Location"] = f"{API_URL}/nas/{nasname}"
    return updated_nas


@router.patch("/users/{username}", tags=["users"], status_code=200, response_model=User, responses={404: error_404})
def patch_user(
    username: str,
    user_update: UserUpdate,
    user_service: UserServiceDep,
    response: Response,
    allow_groups_creation: Annotated[
        bool, Query(description="If set to true, nonexistent groups will be created during user modification")
    ] = False,
    prevent_groups_deletion: Annotated[
        bool, Query(description="If set to false, user groups without any attributes will be deleted")
    ] = True,
):
    try:
        updated_user = user_service.update(
            username=username,
            user_update=user_update,
            allow_groups_creation=allow_groups_creation,
            prevent_groups_deletion=prevent_groups_deletion,
        )
    except ServiceExceptions.UserNotFound as exc:
        raise HTTPException(404, str(exc))
    except (
        ServiceExceptions.GroupNotFound,
        ServiceExceptions.GroupWouldBeDeleted,
        ServiceExceptions.UserWouldBeDeleted,
    ) as exc:
        raise HTTPException(422, str(exc))

    response.headers["Location"] = f"{API_URL}/users/{username}"
    return updated_user


@router.patch("/groups/{groupname}", tags=["groups"], status_code=200, response_model=Group, responses={404: error_404})
def patch_group(
    groupname: str,
    group_update: GroupUpdate,
    group_service: GroupServiceDep,
    response: Response,
    allow_users_creation: Annotated[
        bool, Query(description="If set to true, nonexistent users will be created during group modification")
    ] = False,
    prevent_users_deletion: Annotated[
        bool, Query(description="If set to false, group users without any attributes will be deleted")
    ] = True,
):
    try:
        updated_group = group_service.update(
            groupname=groupname,
            group_update=group_update,
            allow_users_creation=allow_users_creation,
            prevent_users_deletion=prevent_users_deletion,
        )
    except ServiceExceptions.GroupNotFound as exc:
        raise HTTPException(404, str(exc))
    except (
        ServiceExceptions.UserNotFound,
        ServiceExceptions.UserWouldBeDeleted,
        ServiceExceptions.GroupWouldBeDeleted,
    ) as exc:
        raise HTTPException(422, str(exc))

    response.headers["Location"] = f"{API_URL}/groups/{groupname}"
    return updated_group


# API is now ready!
app = FastAPI(title="FreeRADIUS REST API")
app.include_router(router)
