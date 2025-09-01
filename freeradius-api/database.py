from importlib import import_module

from settings import settings

# Dynamically import the DB driver
db_driver = import_module(settings.db_driver)


# Just a util to obtain a new DB session using given DB settings
def db_connect():
    return db_driver.connect(user=settings.db_user, password=settings.db_pass, host=settings.db_host, database=settings.db_name)
