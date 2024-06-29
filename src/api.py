from typing import List

from fastapi import APIRouter, FastAPI, HTTPException, Response
from pydantic import BaseModel

from .config import AppSettings
from .database import get_db_connection
from .pyfreeradius import (Group, GroupRepository, GroupUpdate, Nas,
                           NasRepository, NasUpdate, User, UserRepository,
                           UserUpdate)

SETTINGS = AppSettings()

# Initialize the database connection
db_connection = get_db_connection(SETTINGS.db_type, SETTINGS.db_host, SETTINGS.db_username, SETTINGS.db_password, SETTINGS.db_database)

# Load the FreeRADIUS repositories
user_repo = UserRepository(db_connection, SETTINGS.db_tables)
group_repo = GroupRepository(db_connection, SETTINGS.db_tables)
nas_repo = NasRepository(db_connection, SETTINGS.db_tables)


# Error model and responses
class RadAPIError(BaseModel):
    detail: str


e404_response = {404: {'model': RadAPIError, 'description': 'Item not found'}}
e409_response = {409: {'model': RadAPIError, 'description': 'Item already exists'}}

# Our API router and routes
router = APIRouter()


@router.get('/')
def read_root():
    return {'Welcome!': f'API docs is available at {SETTINGS.api_url}/docs'}


@router.get('/nas', tags=['nas'], status_code=200, response_model=List[str])
def get_nas(response: Response, from_nasname: str = None):
    nasnames = nas_repo.find_nasnames(from_nasname)
    if nasnames:
        last_nasname = nasnames[-1]
        response.headers['Link'] = f'<{SETTINGS.api_url}/nas?from_nasname={last_nasname}>; rel="next"'
    return nasnames


@router.get('/users', tags=['users'], status_code=200, response_model=List[str])
def get_users(response: Response, from_username: str = None):
    usernames = user_repo.find_usernames(from_username)
    if usernames:
        last_username = usernames[-1]
        response.headers['Link'] = f'<{SETTINGS.api_url}/users?from_username={last_username}>; rel="next"'
    return usernames


@router.get('/groups', tags=['groups'], status_code=200, response_model=List[str])
def get_groups(response: Response, from_groupname: str = None):
    groupnames = group_repo.find_groupnames(from_groupname)
    if groupnames:
        last_groupname = groupnames[-1]
        response.headers['Link'] = f'<{SETTINGS.api_url}/groups?from_groupname={last_groupname}>; rel="next"'
    return groupnames


@router.get('/nas/{nasname}', tags=['nas'], status_code=200, response_model=Nas, responses={**e404_response})
def get_nas(nasname: str):
    nas = nas_repo.find_one(nasname)
    if not nas:
        raise HTTPException(404, 'Given NAS does not exist')
    return nas


@router.get('/users/{username}', tags=['users'], status_code=200, response_model=User, responses={**e404_response})
def get_user(username: str):
    user = user_repo.find_one(username)
    if not user:
        raise HTTPException(404, 'Given user does not exist')
    return user


@router.get('/groups/{groupname}', tags=['groups'], status_code=200, response_model=Group, responses={**e404_response})
def get_group(groupname: str):
    group = group_repo.find_one(groupname)
    if not group:
        raise HTTPException(404, 'Given group does not exist')
    return group


@router.post('/nas', tags=['nas'], status_code=201, response_model=Nas, responses={**e409_response})
def post_nas(nas: Nas, response: Response):
    if nas_repo.exists(nas.nasname):
        raise HTTPException(409, 'Given NAS already exists')

    nas_repo.add(nas)
    response.headers['Location'] = f'{SETTINGS.api_url}/nas/{nas.nasname}'
    return nas


@router.post('/users', tags=['users'], status_code=201, response_model=User, responses={**e409_response})
def post_user(user: User, response: Response):
    if user_repo.exists(user.username):
        raise HTTPException(409, 'Given user already exists')

    for group in user.groups:
        if not group_repo.exists(group.groupname):
            raise HTTPException(422, f"Given group '{group.groupname}' does not exist: create it first")

    user_repo.add(user)
    response.headers['Location'] = f'{SETTINGS.api_url}/users/{user.username}'
    return user


@router.post('/groups', tags=['groups'], status_code=201, response_model=Group, responses={**e409_response})
def post_group(group: Group, response: Response):
    if group_repo.exists(group.groupname):
        raise HTTPException(409, 'Given group already exists')

    for user in group.users:
        if not user_repo.exists(user.username):
            raise HTTPException(422, f"Given user '{user.username}' does not exist: create it first")

    group_repo.add(group)
    response.headers['Location'] = f'{SETTINGS.api_url}/groups/{group.groupname}'
    return group


@router.patch('/nas/{nasname}', tags=['nas'], status_code=200, response_model=Nas, responses={**e409_response})
def patch_nas(nasname: str, nas: NasUpdate, response: Response):
    if not nas_repo.exists(nasname):
        raise HTTPException(404, 'Given NAS does not exist')

    nas_repo.update(nasname, nas)
    response.headers['Location'] = f'{API_URL}/nas/{nas.nasname}'
    return nas


@router.patch('/users/{username}', tags=['users'], status_code=200, response_model=User, responses={**e409_response})
def patch_user(username: str, user: UserUpdate, response: Response):
    if not user_repo.exists(username):
        raise HTTPException(404, detail='Given user does not exist')

    for group in user.groups or []:
        if not group_repo.exists(group.groupname):
            raise HTTPException(422, f"Given group '{group.groupname}' does not exist: create it first")

    user_repo.update(username, user)
    response.headers['Location'] = f'{API_URL}/users/{user.username}'
    return user


@router.patch('/groups/{groupname}', tags=['groups'], status_code=200, response_model=Group, responses={**e409_response})
def patch_group(groupname: str, group: GroupUpdate, response: Response):
    if not group_repo.exists(groupname):
        raise HTTPException(404, 'Given group does not exist')

    for user in group.users or []:
        if not user_repo.exists(user.username):
            raise HTTPException(422, f"Given user '{user.username}' does not exist: create it first")

    current_group = group_repo.find_one(groupname)
    if (not current_group.replies and group.replies == []) and (not current_group.checks and group.checks == []):
        raise HTTPException(422, 'Group must have at least one check or one reply attribute')

    group_repo.update(groupname, group)
    response.headers['Location'] = f'{API_URL}/groups/{group.groupname}'
    return group


@router.delete('/nas/{nasname}', tags=['nas'], status_code=204, responses={**e404_response})
def delete_nas(nasname: str):
    if not nas_repo.exists(nasname):
        raise HTTPException(404, 'Given NAS does not exist')

    nas_repo.remove(nasname)


@router.delete('/users/{username}', tags=['users'], status_code=204, responses={**e404_response})
def delete_user(username: str):
    if not user_repo.exists(username):
        raise HTTPException(404, detail='Given user does not exist')

    user_repo.remove(username)


@router.delete('/groups/{groupname}', tags=['groups'], status_code=204, responses={**e404_response})
def delete_group(groupname: str, ignore_users: bool = False):
    if not group_repo.exists(groupname):
        raise HTTPException(404, 'Given group does not exist')

    if group_repo.has_users(groupname) and not ignore_users:
        raise HTTPException(422, "Given group has users: "
                                 "remove them first or set 'ignore_users' flag to True")

    group_repo.remove(groupname)


# API is now ready!
app = FastAPI(title='FreeRADIUS REST API')
app.include_router(router)
