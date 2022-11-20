from pyfreeradius import RadTables

# Uncomment the appropriate line to load the DB-API 2.0 (PEP 249) enabled driver
from mysql.connector import connect
#from pymysql import connect
#from pymssql import connect
#from psycopg2 import connect
#from sqllite3 import connect
#from oracledb import connect
#from <DRIVER> import connect

# DB connection and table names
db_connection = connect(user='raduser', password='radpass', host='mydb', database='raddb')
db_tables = RadTables()
"""
If you use different table names:
db_tables = RadTables(
    radcheck='my-radcheck',
    radreply='my-radreply',
    radgroupcheck='my-radgroupcheck',
    radgroupreply='my-radgroupreply',
    radusergroup='my-radusergroup',
    nas='my-nas'
)
"""
