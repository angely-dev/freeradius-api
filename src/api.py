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


@router.post('/nas', tags=['nas'], status_code=201, response_model=Nas, responses={**e409_response})
def add_nas(nas: Nas, response: Response):
    if nas_repo.exists(nas.nasname):
        raise HTTPException(409, 'Given NAS already exists')
    nas_repo.add(nas)
    response.headers['Location'] = f'{SETTINGS.api_url}/nas/{nas.nasname}'
    return nas


@router.put('/nas/{nasname}', tags=['nas'], status_code=200, response_model=Nas, responses={**e404_response})
def replace_nas(nasname: str, nas: Nas):
    if not nas_repo.exists(nasname):
        raise HTTPException(404, 'Given NAS does not exist')
    nas_repo.update(nasname, NasUpdate(
        shortname=nas.shortname,
        type=nas.type,
        ports=nas.ports,
        secret=nas.secret,
        server=nas.server,
        community=nas.community,
        description=nas.description
    ))
    return nas


@router.patch('/nas/{nasname}', tags=['nas'], status_code=200, response_model=Nas, responses={**e404_response})
def update_nas(nasname: str, nas: NasUpdate):
    if not nas_repo.exists(nasname):
        raise HTTPException(404, 'Given NAS does not exist')
    nas_repo.update(nasname, nas)
    return nas_repo.find_one(nasname)


@router.delete('/nas/{nasname}', tags=['nas'], status_code=204, responses={**e404_response})
def delete_nas(nasname: str):
    if not nas_repo.exists(nasname):
        raise HTTPException(404, 'Given NAS does not exist')
    nas_repo.delete(nasname)


@router.get('/users/{username}', tags=['users'], status_code=200, response_model=User, responses={**e404_response})
def get_user(username: str):
    user = user_repo.find_one(username)
    if not user:
        raise HTTPException(404, 'Given user does not exist')
    return user


@router.post('/users', tags=['users'], status_code=201, response_model=User, responses={**e409_response})
def add_user(user: User, response: Response):
    if user_repo.exists(user.username):
        raise HTTPException(409, 'Given user already exists')
    user_repo.add(user)
    response.headers['Location'] = f'{SETTINGS.api_url}/users/{user.username}'
    return user


@router.put('/users/{username}', tags=['users'], status_code=200, response_model=User, responses={**e404_response})
def replace_user(username: str, user: User):
    if not user_repo.exists(username):
        raise HTTPException(404, 'Given user does not exist')
    user_repo.update(username, UserUpdate(
        checks=user.checks,
        replies=user.replies,
        groups=user.groups
    ))
    return user


@router.patch('/users/{username}', tags=['users'], status_code=200, response_model=User, responses={**e404_response})
def update_user(username: str, user: UserUpdate):
    if not user_repo.exists(username):
        raise HTTPException(404, 'Given user does not exist')
    user_repo.update(username, user)
    return user_repo.find_one(username)


@router.delete('/users/{username}', tags=['users'], status_code=204, responses={**e404_response})
def delete_user(username: str):
    if not user_repo.exists(username):
        raise HTTPException(404, 'Given user does not exist')
    user_repo.delete(username)


@router.get('/groups/{groupname}', tags=['groups'], status_code=200, response_model=Group, responses={**e404_response})
def get_group(groupname: str):
    group = group_repo.find_one(groupname)
    if not group:
        raise HTTPException(404, 'Given group does not exist')
    return group


@router.post('/groups', tags=['groups'], status_code=201, response_model=Group, responses={**e409_response})
def add_group(group: Group, response: Response):
    if group_repo.exists(group.groupname):
        raise HTTPException(409, 'Given group already exists')
    group_repo.add(group)
    response.headers['Location'] = f'{SETTINGS.api_url}/groups/{group.groupname}'
    return group


@router.put('/groups/{groupname}', tags=['groups'], status_code=200, response_model=Group, responses={**e404_response})
def replace_group(groupname: str, group: Group):
    if not group_repo.exists(groupname):
        raise HTTPException(404, 'Given group does not exist')
    group_repo.update(groupname, GroupUpdate(
        checks=group.checks,
        replies=group.replies
    ))
    return group


@router.patch('/groups/{groupname}', tags=['groups'], status_code=200, response_model=Group, responses={**e404_response})
def update_group(groupname: str, group: GroupUpdate):
    if not group_repo.exists(groupname):
        raise HTTPException(404, 'Given group does not exist')
    group_repo.update(groupname, group)
    return group_repo.find_one(groupname)


@router.delete('/groups/{groupname}', tags=['groups'], status_code=204, responses={**e404_response})
def delete_group(groupname: str):
    if not group_repo.exists(groupname):
        raise HTTPException(404, 'Given group does not exist')
    group_repo.delete(groupname)


# Create the FastAPI app
app = FastAPI(title='FreeRADIUS API', description='A RESTful API to manage FreeRADIUS database entries', version='0.1.0')
app.include_router(router)