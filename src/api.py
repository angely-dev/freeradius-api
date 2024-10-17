from dependencies import UserRepositoryDep, GroupRepositoryDep, NasRepositoryDep
from fastapi import FastAPI, APIRouter, Response, HTTPException
from pydantic import BaseModel
from pyfreeradius.models import User, Group, Nas
from settings import API_URL

#
# We want our REST API endpoints to be KISS!
# Only GET/POST/DELETE methods are implemented; no PUT/PATCH methods.
# To modify an existing object, first remove it and then recreate it.
#


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


@router.get("/nas", tags=["nas"], status_code=200, response_model=list[str])
def get_nases(nas_repo: NasRepositoryDep, response: Response, from_nasname: str | None = None):
    nasnames = nas_repo.find_nasnames(from_nasname)
    if nasnames:
        last_nasname = nasnames[-1]
        response.headers["Link"] = f'<{API_URL}/nas?from_nasname={last_nasname}>; rel="next"'
    return nasnames


@router.get("/users", tags=["users"], status_code=200, response_model=list[str])
def get_users(user_repo: UserRepositoryDep, response: Response, from_username: str | None = None):
    usernames = user_repo.find_usernames(from_username)
    if usernames:
        last_username = usernames[-1]
        response.headers["Link"] = f'<{API_URL}/users?from_username={last_username}>; rel="next"'
    return usernames


@router.get("/groups", tags=["groups"], status_code=200, response_model=list[str])
def get_groups(group_repo: GroupRepositoryDep, response: Response, from_groupname: str | None = None):
    groupnames = group_repo.find_groupnames(from_groupname)
    if groupnames:
        last_groupname = groupnames[-1]
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
def post_user(user: User, user_repo: UserRepositoryDep, group_repo: GroupRepositoryDep, response: Response):
    if user_repo.exists(user.username):
        raise HTTPException(409, "Given user already exists")

    for group in user.groups:
        if not group_repo.exists(group.groupname):
            raise HTTPException(422, f"Given group '{group.groupname}' does not exist: create it first")

    user_repo.add(user)
    response.headers["Location"] = f"{API_URL}/users/{user.username}"
    return user


@router.post("/groups", tags=["groups"], status_code=201, response_model=Group, responses={409: error_409})
def post_group(group: Group, group_repo: GroupRepositoryDep, user_repo: UserRepositoryDep, response: Response):
    if group_repo.exists(group.groupname):
        raise HTTPException(409, "Given group already exists")

    for user in group.users:
        if not user_repo.exists(user.username):
            raise HTTPException(422, f"Given user '{user.username}' does not exist: create it first")

    group_repo.add(group)
    response.headers["Location"] = f"{API_URL}/groups/{group.groupname}"
    return group


@router.delete("/nas/{nasname}", tags=["nas"], status_code=204, responses={404: error_404})
def delete_nas(nasname: str, nas_repo: NasRepositoryDep):
    if not nas_repo.exists(nasname):
        raise HTTPException(404, "Given NAS does not exist")

    nas_repo.remove(nasname)


@router.delete("/users/{username}", tags=["users"], status_code=204, responses={404: error_404})
def delete_user(username: str, user_repo: UserRepositoryDep):
    if not user_repo.exists(username):
        raise HTTPException(404, detail="Given user does not exist")

    user_repo.remove(username)


@router.delete("/groups/{groupname}", tags=["groups"], status_code=204, responses={404: error_404})
def delete_group(groupname: str, group_repo: GroupRepositoryDep, ignore_users: bool = False):
    if not group_repo.exists(groupname):
        raise HTTPException(404, "Given group does not exist")

    if group_repo.has_users(groupname) and not ignore_users:
        raise HTTPException(422, "Given group has users: remove them first or set 'ignore_users' flag to True")

    group_repo.remove(groupname)


# API is now ready!
app = FastAPI(title="FreeRADIUS REST API")
app.include_router(router)
