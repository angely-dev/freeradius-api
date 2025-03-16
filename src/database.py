from importlib import import_module

from settings import DB_DRIVER, DB_HOST, DB_NAME, DB_PASS, DB_USER

# Dynamically import the DB driver
db_driver = import_module(DB_DRIVER)


# Just a util to obtain a new DB session using given DB settings
def db_connect():
    return db_driver.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, database=DB_NAME)
