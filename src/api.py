from database import db_connection, db_tables
from fastapi import FastAPI, APIRouter, Response, HTTPException
from pyfreeradius import User, Group, Nas
from pyfreeradius import UserRepository, GroupRepository, NasRepository
from typing import List

#
# We want our REST API endpoints to be KISS!
# Only GET/POST/DELETE methods are implemented; no PUT/PATCH methods.
# To modify an existing object, first remove it and then recreate it.
#

# Load the FreeRADIUS repositories
user_repo = UserRepository(db_connection, db_tables)
group_repo = GroupRepository(db_connection, db_tables)
nas_repo = NasRepository(db_connection, db_tables)

# API_URL will be used to set the "Location" header field
# after a resource has been created (POST) as per RFC 7231
API_URL = 'http://localhost:8000'

# Our API router and routes
router = APIRouter()

@router.get('/')
def read_root():
    return {'Welcome!': f'API docs is available at {API_URL}/docs'}

@router.get('/nas', tags=['nas'], status_code=200, response_model=List[str])
async def get_nas():
    return nas_repo.find_all_nasnames()

@router.get('/users', tags=['users'], status_code=200, response_model=List[str])
async def get_users():
    return user_repo.find_all_usernames()

@router.get('/groups', tags=['groups'], status_code=200, response_model=List[str])
async def get_groups():
    return group_repo.find_all_groupnames()

@router.get('/nas/{nasname}', tags=['nas'], status_code=200, response_model=Nas)
async def get_nas(nasname: str):
    nas = nas_repo.find_one(nasname)
    if not nas:
        raise HTTPException(404, 'Given NAS does not exist')
    return nas

@router.get('/users/{username}', tags=['users'], status_code=200, response_model=User)
async def get_user(username: str):
    user = user_repo.find_one(username)
    if not user:
        raise HTTPException(404, 'Given user does not exist')
    return user

@router.get('/groups/{groupname}', tags=['groups'], status_code=200, response_model=Group)
async def get_group(groupname: str):
    group = group_repo.find_one(groupname)
    if not group:
        raise HTTPException(404, 'Given group does not exist')
    return group

@router.post('/nas', tags=['nas'], status_code=201, response_model=Nas)
async def post_nas(nas: Nas, response: Response):
    if nas_repo.exists(nas.nasname):
       raise HTTPException(422, 'Given NAS already exists')

    nas_repo.add(nas)
    response.headers['Location'] = f'{API_URL}/nas/{nas.nasname}'
    return nas

@router.post('/users', tags=['users'], status_code=201, response_model=User)
async def post_user(user: User, response: Response):
    if user_repo.exists(user.username):
        raise HTTPException(422, 'Given user already exists')

    for group in user.groups:
        if not group_repo.exists(group.groupname):
            raise HTTPException(422, f"Given group '{group.groupname}' does not exist: create it first")

    user_repo.add(user)
    response.headers['Location'] = f'{API_URL}/users/{user.username}'
    return user

@router.post('/groups', tags=['groups'], status_code=201, response_model=Group)
async def post_group(group: Group, response: Response):
    if group_repo.exists(group.groupname):
        raise HTTPException(422, 'Given group already exists')

    for user in group.users:
        if not user_repo.exists(user.username):
            raise HTTPException(422, f"Given user '{user.username}' does not exist: create it first")

    group_repo.add(group)
    response.headers['Location'] = f'{API_URL}/groups/{group.groupname}'
    return group

@router.delete('/nas/{nasname}', tags=['nas'], status_code=204)
async def delete_nas(nasname: str):
    if not nas_repo.exists(nasname):
        raise HTTPException(404, 'Given NAS does not exist')

    nas_repo.remove(nasname)

@router.delete('/users/{username}', tags=['users'], status_code=204)
async def delete_user(username: str):
    if not user_repo.exists(username):
        raise HTTPException(404, detail='Given user does not exist')

    user_repo.remove(username)

@router.delete('/groups/{groupname}', tags=['groups'], status_code=204)
async def delete_group(groupname: str, ignore_users: bool = False):
    if not group_repo.exists(groupname):
        raise HTTPException(404, 'Given group does not exist')

    if group_repo.has_users(groupname) and not ignore_users:
        raise HTTPException(422, "Given group has users: "
                                 "remove them first or set 'ignore_users' flag to True")

    group_repo.remove(groupname)

# API is now ready!
app = FastAPI(title='FreeRADIUS REST API')
app.include_router(router)
