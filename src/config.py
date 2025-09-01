from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RadTables(BaseModel):
    radcheck: str = "radcheck"
    radreply: str = "radreply"
    radgroupcheck: str = "radgroupcheck"
    radgroupreply: str = "radgroupreply"
    radusergroup: str = "radusergroup"
    nas: str = "nas"


class AppSettings(BaseSettings):
    db_type: str = "mysql"
    db_host: str = "localhost"
    db_username: str = "raduser"
    db_password: str = "radpass"
    db_database: str = "raddb"
    db_tables: RadTables = RadTables()

    # api_url will be used to set the "Location" header field
    # after a resource has been created (POST) as per RFC 7231
    # and the "Link" header field (pagination) as per RFC 8288
    api_url: str = "http://localhost:8000"

    # API Key Authentication
    api_key_enabled: bool = False
    api_key: str = "your-api-key-change-this-in-production"
    api_key_header: str = "X-API-Key"

    @field_validator("api_key_enabled", mode="before")
    def validate_api_key_enabled(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
