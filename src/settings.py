# Uncomment the appropriate line matching your DB-API 2.0 (PEP 249) enabled driver
DB_DRIVER = "mysql.connector"
# DB_DRIVER = "pymysql"
# DB_DRIVER = "pymssql"
# DB_DRIVER = "psycopg2"
# DB_DRIVER = "sqllite3"
# DB_DRIVER = "oracledb"
# DB_DRIVER = "<DRIVER>"

# Database connection settings
DB_NAME = "raddb"
DB_USER = "raduser"
DB_PASS = "radpass"
DB_HOST = "mydb"

# Database table names
RADCHECK = "radcheck"
RADREPLY = "radreply"
RADGROUPCHECK = "radgroupcheck"
RADGROUPREPLY = "radgroupreply"
RADUSERGROUP = "radusergroup"
NAS = "nas"

# Number of results per page for pagination
PER_PAGE = 100

# API_URL will be used to set the "Location" header field
# after a resource has been created (POST) as per RFC 7231
# and the "Link" header field (pagination) as per RFC 8288
API_URL = "http://localhost:8000"
