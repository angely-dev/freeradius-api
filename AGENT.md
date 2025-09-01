# AI Agent Guidelines for FreeRADIUS API

This document provides guidelines for AI agents working on the FreeRADIUS API project.

## Project Overview

This is a Python REST API built with FastAPI that provides an object-oriented interface to FreeRADIUS databases. It supports MySQL, MariaDB, PostgreSQL, and SQLite databases and includes features like:

- CRUD operations for NAS devices, users, and groups
- Keyset pagination for performance
- JSON Merge Patch updates (RFC 7396)
- Optional API key authentication
- Docker setup for testing

## Development Setup

### Prerequisites

- Python 3.10+
- Database (MySQL/MariaDB/PostgreSQL/SQLite)
- Docker (optional, for testing)

### Installation

1. Clone the repository and navigate to the project directory
2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Modify the values in `.env` as needed
   - Or set environment variables directly

   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

   Key environment variables:
   - `APP_ENV`: Application execution environment (dev: load sample data, production: nothing)
   - `DB_DRIVER`: Database driver (mysql.connector, psycopg2, sqlite3, etc.)
   - `DB_NAME`: Database name
   - `DB_USER`: Database username
   - `DB_PASS`: Database password
   - `DB_HOST`: Database host
   - `API_URL`: Base URL for the API
   - `API_PORT`: Port for the API server

### Running the API

```bash
cd freeradius-api
uvicorn api:app --reload
```

The API will be available at the configured `API_URL` (default: <http://localhost:8000>) with documentation at `{API_URL}/docs`

## Configuration

The application uses environment-based configuration with Pydantic BaseSettings. All configuration is centralized in the `Settings` class in `freeradius-api/settings.py`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_DRIVER` | `mysql.connector` | Database driver to use |
| `DB_NAME` | `raddb` | Database name |
| `DB_USER` | `raduser` | Database username |
| `DB_PASS` | `radpass` | Database password |
| `DB_HOST` | `mydb` | Database host |
| `DB_PORT` | `3306` | Database port (optional) |
| `API_URL` | `http://localhost:8000` | Base URL for API responses |
| `API_HOST` | `0.0.0.0` | Host to bind the API server |
| `API_PORT` | `8000` | Port for the API server |
| `ITEMS_PER_PAGE` | `100` | Items per page for pagination |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `API_KEY_ENABLED` | `false` | Enable API key authentication |
| `API_KEY` | `None` | API key for authentication |
| `API_KEY_HEADER` | `X-API-Key` | Header name for API key |

### Configuration File

You can also create a `.env` file in the project root:

```bash
cp .env.example .env
# Edit .env with your values
```

The application will automatically load environment variables from the `.env` file.

## Coding Conventions

### Python Style

- **Line length**: 120 characters (configured in pyproject.toml)
- **Linting**: Ruff with isort extension enabled
- **Type checking**: MyPy recommended
- **Imports**: Follow PEP 8, use absolute imports

### Code Structure

- Main API code in `freeradius-api/` directory
- Tests in `tests/` directory
- Configuration in `freeradius-api/settings.py`
- Database operations in `freeradius-api/database.py`
- API endpoints in `freeradius-api/api.py`

### Key Files

- `freeradius-api/api.py`: FastAPI application and endpoints
- `freeradius-api/database.py`: Database connection and operations
- `freeradius-api/settings.py`: Configuration settings
- `freeradius-api/dependencies.py`: FastAPI dependencies

## Testing

### Running Tests

```bash
pytest
```

### Test Coverage

```bash
pytest --cov=freeradius-api --cov-report=html
```

### Test Structure

- Unit tests in `tests/test_api.py`
- Use pytest framework
- Include httpx for API testing
- Mock database operations where appropriate

## Code Quality

### Linting

```bash
ruff check .
```

### Auto-fix

```bash
ruff check . --fix
```

### Type Checking

```bash
mypy freeradius-api/
```

### Pre-commit Hooks

The project uses pre-commit hooks. Install and run:

```bash
pre-commit install
pre-commit run --all-files
```

## Database Operations

### Supported Databases

- MySQL/MariaDB
- PostgreSQL
- SQLite

### Schema

The API works with standard FreeRADIUS database tables:

- `radcheck`: User check attributes
- `radreply`: User reply attributes
- `radgroupcheck`: Group check attributes
- `radgroupreply`: Group reply attributes
- `radusergroup`: User-group relationships
- `nas`: NAS devices

### Database Configuration

Configure in `freeradius-api/settings.py`:

```python
DB_DRIVER = "mysql.connector"  # or psycopg, pymysql, etc.
DB_NAME = "raddb"
DB_USER = "raduser"
DB_PASS = "radpass"
DB_HOST = "localhost"
```

## API Design Patterns

### Endpoints

- `GET /nas`: List NAS devices
- `GET /users`: List users
- `GET /groups`: List groups
- `POST /nas`: Create NAS device
- `POST /users`: Create user
- `POST /groups`: Create group
- `PATCH /nas/{id}`: Update NAS device
- `PATCH /users/{id}`: Update user
- `PATCH /groups/{id}`: Update group
- `DELETE /nas/{id}`: Delete NAS device
- `DELETE /users/{id}`: Delete user
- `DELETE /groups/{id}`: Delete group

### Pagination

- Uses keyset pagination (not offset)
- Pagination info in HTTP Link headers
- Default limit: 100 items per page

### Update Strategy

- Follows RFC 7396 (JSON Merge Patch)
- Omitted fields are not modified
- `None` values reset fields to defaults
- List fields can only be completely replaced

## Docker Development

### Quick Start

```bash
cd docker
docker compose up -d
```

This starts:

- MySQL database with FreeRADIUS schema
- phpMyAdmin for database management
- The API server

### Docker Files

- `docker/docker-compose.yml`: Multi-service setup
- `docker/Dockerfile`: API container
- `docker/freeradius-mysql/`: Database initialization scripts

## Security Considerations

### Authentication

- Optional API key authentication via environment variables
- Enable with `API_KEY_ENABLED=true` and set `API_KEY` value
- Use HTTPS in production
- Never commit API keys to version control
- API key is read from environment variables, not hardcoded

### Database Security

- Use strong passwords
- Limit database user privileges
- Use parameterized queries (handled by pyfreeradius)
- Validate all input data

## Deployment

### Production Considerations

- Set `API_URL` in settings.py
- Configure proper database credentials
- Enable authentication with `API_KEY_ENABLED=true` and set a strong `API_KEY`
- Use reverse proxy (nginx, etc.)
- Set up monitoring and logging
- Use environment variables for sensitive data

### Environment Variables

Consider using environment variables for:

- Database credentials
- API keys
- API URL
- Database host/port

## Common Tasks

### Adding New Endpoints

1. Add route in `freeradius-api/api.py`
2. Implement database operations in `freeradius-api/database.py`
3. Add tests in `tests/test_api.py`
4. Update documentation

### Database Schema Changes

1. Update table configurations in `freeradius-api/settings.py`
2. Modify database operations accordingly
3. Update tests
4. Update Docker initialization scripts if needed

### Adding Authentication

The API now supports API key authentication which can be enabled through environment variables:

1. Set `API_KEY_ENABLED=true` in your environment or `.env` file
2. Set `API_KEY=your-secret-key` in your environment or `.env` file
3. Optionally change the header name with `API_KEY_HEADER=X-API-Key` (default)

When enabled, all endpoints will require authentication via the specified header.

## Troubleshooting

### Common Issues

- Database connection errors: Check credentials and network
- Import errors: Ensure virtual environment is activated
- Test failures: Check database state and test data
- Docker issues: Check port conflicts and Docker daemon

### Debugging

- Use `--reload` flag with uvicorn for development
- Check logs in Docker containers
- Use pdb or debugger for Python code
- Verify database queries with phpMyAdmin

## Contributing

### Commit Messages

- Use clear, descriptive commit messages
- Follow conventional commit format if possible
- Reference issue numbers when applicable

### Pull Requests

- Include tests for new features
- Update documentation as needed
- Ensure all checks pass (lint, tests, type check)
- Provide clear description of changes

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pyfreeradius Documentation](https://github.com/angely-dev/pyfreeradius)
- [FreeRADIUS Documentation](https://freeradius.org/documentation/)
- [RFC 7396 - JSON Merge Patch](https://datatracker.ietf.org/doc/html/rfc7396)
- [RFC 8288 - Link Header](https://www.rfc-editor.org/rfc/rfc8288)

