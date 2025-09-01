from pydantic import Field
from pydantic_settings import BaseSettings
from pyfreeradius import RadTables


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database configuration
    db_driver: str = Field(
        default="mysql.connector",
        description="Database driver (mysql.connector, pymysql, psycopg2, sqlite3, etc.)",
        validation_alias="DB_DRIVER",
    )
    db_name: str = Field(default="raddb", description="Database name", validation_alias="DB_NAME")
    db_user: str = Field(default="raduser", description="Database username", validation_alias="DB_USER")
    db_pass: str = Field(default="radpass", description="Database password", validation_alias="DB_PASS")
    db_host: str = Field(default="mydb", description="Database host", validation_alias="DB_HOST")
    db_port: int | None = Field(default=None, description="Database port (optional)", validation_alias="DB_PORT")

    # API configuration
    api_url: str = Field(
        default="http://localhost:8000", description="API base URL for Location and Link headers", validation_alias="API_URL"
    )
    api_host: str = Field(default="0.0.0.0", description="API server host", validation_alias="API_HOST")
    api_port: int = Field(default=8000, description="API server port", validation_alias="API_PORT")

    # Pagination settings
    items_per_page: int = Field(
        default=100, description="Number of items per page for pagination", validation_alias="ITEMS_PER_PAGE", ge=1, le=1000
    )

    # Database table names (customizable)
    table_radcheck: str = Field(
        default="radcheck", description="Table name for user check attributes", validation_alias="TABLE_RADCHECK"
    )
    table_radreply: str = Field(
        default="radreply", description="Table name for user reply attributes", validation_alias="TABLE_RADREPLY"
    )
    table_radgroupcheck: str = Field(
        default="radgroupcheck", description="Table name for group check attributes", validation_alias="TABLE_RADGROUPCHECK"
    )
    table_radgroupreply: str = Field(
        default="radgroupreply", description="Table name for group reply attributes", validation_alias="TABLE_RADGROUPREPLY"
    )
    table_radusergroup: str = Field(
        default="radusergroup", description="Table name for user-group relationships", validation_alias="TABLE_RADUSERGROUP"
    )
    table_nas: str = Field(default="nas", description="Table name for NAS devices", validation_alias="TABLE_NAS")

    # Application settings
    env: str = Field(default="dev", description="Environment (dev, staging, prod)", validation_alias="ENV")
    debug: bool = Field(default=False, description="Enable debug mode", validation_alias="DEBUG")
    log_level: str = Field(default="INFO", description="Logging level", validation_alias="LOG_LEVEL")

    # CORS settings
    cors_origins_str: str = Field(
        default="*", description="Comma-separated list of allowed CORS origins", validation_alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS", validation_alias="CORS_ALLOW_CREDENTIALS"
    )
    cors_allow_methods_str: str = Field(
        default="*", description="Comma-separated list of allowed CORS methods", validation_alias="CORS_ALLOW_METHODS"
    )
    cors_allow_headers_str: str = Field(
        default="*", description="Comma-separated list of allowed CORS headers", validation_alias="CORS_ALLOW_HEADERS"
    )

    # API Authentication
    api_key_enabled: bool = Field(default=False, description="Enable API key authentication", validation_alias="API_KEY_ENABLED")
    api_key: str | None = Field(default=None, description="API key for authentication", validation_alias="API_KEY")
    api_key_header: str = Field(default="X-API-Key", description="Header name for API key", validation_alias="API_KEY_HEADER")

    @property
    def rad_tables(self) -> RadTables:
        """Get the RadTables configuration."""
        return RadTables(
            radcheck=self.table_radcheck,
            radreply=self.table_radreply,
            radgroupcheck=self.table_radgroupcheck,
            radgroupreply=self.table_radgroupreply,
            radusergroup=self.table_radusergroup,
            nas=self.table_nas,
        )

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins_str == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    @property
    def cors_allow_methods(self) -> list[str]:
        """Parse CORS methods from comma-separated string."""
        if self.cors_allow_methods_str == "*":
            return ["*"]
        return [method.strip().upper() for method in self.cors_allow_methods_str.split(",") if method.strip()]

    @property
    def cors_allow_headers(self) -> list[str]:
        """Parse CORS headers from comma-separated string."""
        if self.cors_allow_headers_str == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers_str.split(",") if header.strip()]

    class Config:
        """Pydantic configuration."""

        env_file_encoding = "utf-8"
        case_sensitive = False

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            """Customize settings sources to support multiple environments."""
            # Get the ENV value from environment or default to 'dev'
            import os

            from pydantic_settings import PydanticBaseSettingsSource

            env = os.getenv("ENV", "dev")

            # Define env files in order of precedence
            env_files = [
                f".env.{env}",  # Environment-specific file (e.g., .env.dev)
                ".env",  # Default env file
            ]

            # Return sources with custom env files
            return (
                init_settings,
                PydanticBaseSettingsSource(cls, env_file=env_files, env_file_encoding="utf-8"),
                file_secret_settings,
            )


# Create global settings instance
settings = Settings()
