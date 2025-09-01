def get_db_connection(db_type: str, db_host: str, db_username: str, db_password: str, db_database: str):
    """ Get a database connection """
    if db_type == 'mysql':
        from mysql.connector import connect
        return connect(user=db_username, password=db_password, host=db_host, database=db_database)
    if db_type == 'mssql':
        from pymssql import connect
        return connect(user=db_username, password=db_password, server=db_host, database=db_database)
    if db_type == 'postgres':
        from psycopg2 import connect
        return connect(user=db_username, password=db_password, host=db_host, database=db_database)
    if db_type == 'sqlite':
        from sqlite3 import connect
        return connect(db_database)
    if db_type == 'oracle':
        from oracledb import connect
        return connect(user=db_username, password=db_password, dsn=db_host)
    raise ValueError('Unsupported database type')