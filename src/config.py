from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class RadTables(BaseModel):
    radcheck: str = 'radcheck'
    radreply: str = 'radreply'
    radgroupcheck: str = 'radgroupcheck'
    radgroupreply: str = 'radgroupreply'
    radusergroup: str = 'radusergroup'
    nas: str = 'nas'


class AppSettings(BaseSettings):
    db_type: str = 'mysql'
    db_host: str = 'localhost'
    db_username: str = 'raduser'
    db_password: str = 'radpass'
    db_database: str = 'raddb'
    db_tables: RadTables = RadTables()

    # api_url will be used to set the "Location" header field
    # after a resource has been created (POST) as per RFC 7231
    # and the "Link" header field (pagination) as per RFC 8288
    api_url: str = 'http://localhost:8000'

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
