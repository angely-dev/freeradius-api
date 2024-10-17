from database import db_connect
from fastapi import Depends
from pyfreeradius.repositories import UserRepository, GroupRepository, NasRepository
from typing import Annotated

#
# Here we use FastAPI Dependency Injection system.
#
# For each API request:
#   - a short-lived DB session will be established,
#   - appropriate repositories will be instantiated.
#


def get_db_session():
    db_session = db_connect()
    yield db_session
    db_session.close()


# Repositories depend on the DB session


def get_user_repository(db_session=Depends(get_db_session)) -> UserRepository:
    return UserRepository(db_session)


def get_group_repository(db_session=Depends(get_db_session)) -> GroupRepository:
    return GroupRepository(db_session)


def get_nas_repository(db_session=Depends(get_db_session)) -> NasRepository:
    return NasRepository(db_session)


# API routes will depend on the repositories
# (using Annotated dependencies for code reuse as per FastAPI doc)

UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
GroupRepositoryDep = Annotated[GroupRepository, Depends(get_group_repository)]
NasRepositoryDep = Annotated[NasRepository, Depends(get_nas_repository)]
