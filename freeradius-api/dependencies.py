from typing import Annotated

from fastapi import Depends

from database import db_connect
from pyfreeradius.repositories import GroupRepository, NasRepository, UserRepository
from pyfreeradius.services import GroupService, NasService, UserService
from settings import REPO_SETTINGS

#
# Here we use FastAPI Dependency Injection system.
#
# For each API request:
#   - a short-lived DB session will be established,
#   - appropriate repositories and services will be instantiated.
#


def get_db_session():
    db_session = db_connect()
    try:
        yield db_session
    except:
        # on any error, we rollback the DB
        db_session.rollback()
        raise
    else:
        # otherwise, we commit the DB
        db_session.commit()
    finally:
        # in any case, we close the DB session
        db_session.close()


# Services depend on the repositories which depend on the DB session


def get_user_service(db_session=Depends(get_db_session)) -> UserService:
    return UserService(
        user_repo=UserRepository(db_session, REPO_SETTINGS),
        group_repo=GroupRepository(db_session, REPO_SETTINGS),
    )


def get_group_service(db_session=Depends(get_db_session)) -> GroupService:
    return GroupService(
        group_repo=GroupRepository(db_session, REPO_SETTINGS),
        user_repo=UserRepository(db_session, REPO_SETTINGS),
    )


def get_nas_service(db_session=Depends(get_db_session)) -> NasService:
    return NasService(nas_repo=NasRepository(db_session, REPO_SETTINGS))


# API routes will depend on the services
# (using Annotated dependencies for code reuse as per FastAPI doc)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
GroupServiceDep = Annotated[GroupService, Depends(get_group_service)]
NasServiceDep = Annotated[NasService, Depends(get_nas_service)]
