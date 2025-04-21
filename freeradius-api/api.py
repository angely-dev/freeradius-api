from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

from dependencies import GroupServiceDep, NasServiceDep, UserServiceDep
from pyfreeradius.models import Group, Nas, User
from pyfreeradius.schemas import GroupUpdate, NasUpdate, UserUpdate
from pyfreeradius.services import ErrorType
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
    nasnames = nas_service.get_all(from_nasname).value
    if nasnames:
        last_nasname = nasnames[-1].nasname
        response.headers["Link"] = f'<{API_URL}/nas?from_nasname={last_nasname}>; rel="next"'
    return nasnames


@router.get("/users", tags=["users"], status_code=200, response_model=list[User])
def get_users(user_service: UserServiceDep, response: Response, from_username: str | None = None):
    usernames = user_service.get_all(from_username).value
    if usernames:
        last_username = usernames[-1].username
        response.headers["Link"] = f'<{API_URL}/users?from_username={last_username}>; rel="next"'
    return usernames


@router.get("/groups", tags=["groups"], status_code=200, response_model=list[Group])
def get_groups(group_service: GroupServiceDep, response: Response, from_groupname: str | None = None):
    groupnames = group_service.get_all(from_groupname).value
    if groupnames:
        last_groupname = groupnames[-1].groupname
        response.headers["Link"] = f'<{API_URL}/groups?from_groupname={last_groupname}>; rel="next"'
    return groupnames


@router.get("/nas/{nasname}", tags=["nas"], status_code=200, response_model=Nas, responses={404: error_404})
def get_nas(nasname: str, nas_service: NasServiceDep):
    result = nas_service.get(nasname)
    if result.error_type == ErrorType.NAS_NOT_FOUND:
        raise HTTPException(404, result.error_info)
    return result.value


@router.get("/users/{username}", tags=["users"], status_code=200, response_model=User, responses={404: error_404})
def get_user(username: str, user_service: UserServiceDep):
    result = user_service.get(username)
    if result.error_type == ErrorType.USER_NOT_FOUND:
        raise HTTPException(404, result.error_info)
    return result.value


@router.get("/groups/{groupname}", tags=["groups"], status_code=200, response_model=Group, responses={404: error_404})
def get_group(groupname: str, group_service: GroupServiceDep):
    result = group_service.get(groupname)
    if result.error_type == ErrorType.GROUP_NOT_FOUND:
        raise HTTPException(404, result.error_info)
    return result.value


@router.post("/nas", tags=["nas"], status_code=201, response_model=Nas, responses={409: error_409})
def post_nas(nas: Nas, nas_service: NasServiceDep, response: Response):
    result = nas_service.create(nas)

    if result.error_type == ErrorType.NAS_ALREADY_EXISTS:
        raise HTTPException(409, result.error_info)

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
    result = user_service.create(user=user, allow_groups_creation=allow_groups_creation)

    if result.error_type == ErrorType.USER_ALREADY_EXISTS:
        raise HTTPException(409, result.error_info)
    if result.error_type == ErrorType.GROUP_NOT_FOUND:
        raise HTTPException(422, result.error_info)

    response.headers["Location"] = f"{API_URL}/users/{user.username}"
    return result.value


@router.post("/groups", tags=["groups"], status_code=201, response_model=Group, responses={409: error_409})
def post_group(
    group: Group,
    group_service: GroupServiceDep,
    response: Response,
    allow_users_creation: Annotated[
        bool, Query(description="If set to true, nonexistent users will be created during group creation")
    ] = False,
):
    result = group_service.create(group=group, allow_users_creation=allow_users_creation)

    if result.error_type == ErrorType.GROUP_ALREADY_EXISTS:
        raise HTTPException(409, result.error_info)
    if result.error_type == ErrorType.USER_NOT_FOUND:
        raise HTTPException(422, result.error_info)

    response.headers["Location"] = f"{API_URL}/groups/{group.groupname}"
    return result.value


@router.delete("/nas/{nasname}", tags=["nas"], status_code=204, responses={404: error_404})
def delete_nas(nasname: str, nas_service: NasServiceDep):
    result = nas_service.delete(nasname)

    if result.error_type == ErrorType.NAS_NOT_FOUND:
        raise HTTPException(404, result.error_info)


@router.delete("/users/{username}", tags=["users"], status_code=204, responses={404: error_404})
def delete_user(
    username: str,
    user_service: UserServiceDep,
    prevent_groups_deletion: Annotated[
        bool, Query(description="If set to false, user groups without any attributes will be deleted")
    ] = True,
):
    result = user_service.delete(username=username, prevent_groups_deletion=prevent_groups_deletion)

    if result.error_type == ErrorType.USER_NOT_FOUND:
        raise HTTPException(404, result.error_info)
    if result.error_type == ErrorType.GROUP_WOULD_BE_DELETED:
        raise HTTPException(422, result.error_info)


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
    result = group_service.delete(
        groupname=groupname, ignore_users=ignore_users, prevent_users_deletion=prevent_users_deletion
    )

    if result.error_type == ErrorType.GROUP_NOT_FOUND:
        raise HTTPException(404, result.error_info)
    if result.error_type in [ErrorType.GROUP_HAS_USERS, ErrorType.USER_WOULD_BE_DELETED]:
        raise HTTPException(422, result.error_info)


@router.patch("/nas/{nasname}", tags=["nas"], status_code=200, response_model=Nas, responses={404: error_404})
def patch_nas(nasname: str, nas_update: NasUpdate, nas_service: NasServiceDep, response: Response):
    result = nas_service.update(nasname=nasname, nas_update=nas_update)

    if result.error_type == ErrorType.NAS_NOT_FOUND:
        raise HTTPException(404, result.error_info)

    response.headers["Location"] = f"{API_URL}/nas/{nasname}"
    return result.value


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
    result = user_service.update(
        username=username,
        user_update=user_update,
        allow_groups_creation=allow_groups_creation,
        prevent_groups_deletion=prevent_groups_deletion,
    )

    if result.error_type == ErrorType.USER_NOT_FOUND:
        raise HTTPException(404, result.error_info)
    if result.error_type in [
        ErrorType.GROUP_NOT_FOUND,
        ErrorType.GROUP_WOULD_BE_DELETED,
        ErrorType.USER_WOULD_BE_DELETED,
    ]:
        raise HTTPException(422, result.error_info)

    response.headers["Location"] = f"{API_URL}/users/{username}"
    return result.value


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
    result = group_service.update(
        groupname=groupname,
        group_update=group_update,
        allow_users_creation=allow_users_creation,
        prevent_users_deletion=prevent_users_deletion,
    )

    if result.error_type == ErrorType.GROUP_NOT_FOUND:
        raise HTTPException(404, result.error_info)
    if result.error_type in [
        ErrorType.USER_NOT_FOUND,
        ErrorType.USER_WOULD_BE_DELETED,
        ErrorType.GROUP_WOULD_BE_DELETED,
    ]:
        raise HTTPException(422, result.error_info)

    response.headers["Location"] = f"{API_URL}/groups/{groupname}"
    return result.value


# API is now ready!
app = FastAPI(title="FreeRADIUS REST API")
app.include_router(router)
