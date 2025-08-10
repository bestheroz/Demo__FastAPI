# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Code Quality and Testing
- **Lint code**: `ruff check`
- **Format code**: `ruff format`
- **Type checking**: `mypy app/`
- **Alternative type checking**: `pyright app/`
- **Run tests**: `pytest`
- **Run tests with coverage**: `pytest --cov=app --cov-report=term-missing`
- **Run single test file**: `pytest tests/test_specific_file.py`
- **Run single test function**: `pytest tests/test_file.py::test_function_name`

### Running the Application
- **Start development server**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Production server**: Uses `uvicorn` with production settings based on `DEPLOYMENT_ENVIRONMENT`

### Package Management
- This project uses **Poetry** for dependency management
- **Install dependencies**: `poetry install`
- **Add new package**: `poetry add <package-name>`
- **Add dev dependency**: `poetry add --group dev <package-name>`

## Architecture Overview

### Project Structure
This is a **FastAPI** application following clean architecture principles:

- **`app/api/`**: API routers and endpoints (v1 versioning)
- **`app/services/`**: Business logic layer
- **`app/models/`**: SQLAlchemy ORM models  
- **`app/schemas/`**: Pydantic schemas for request/response validation
- **`app/dependencies/`**: FastAPI dependencies (auth, database, logging)
- **`app/core/`**: Core functionality (settings, exceptions, codes)
- **`app/utils/`**: Utility functions (JWT, datetime, pagination)
- **`app/types/`**: Type definitions and enums
- **`migrations/`**: SQL migration files (V1__, V2__, etc.)

### Key Architectural Patterns

#### Domain Structure
The application is organized around three main domains:
- **Admin**: Administrative user management with JWT authentication
- **User**: Regular user management with JWT authentication  
- **Notice**: Notice/announcement system

#### Database Architecture
- **Database Session Management**: Custom `DatabaseSessionManager` with read/write separation
- **Connection Pooling**: Configured pool sizes with read-only optimization
- **Dual Session Support**: Separate read-only sessions for query optimization
- **Base Models**: `IdCreated` and `IdCreatedUpdated` for audit trails

#### Authentication & Authorization
- **JWT-based authentication** with separate tokens for different user types
- **Authority-based authorization** using `AuthorityChecker` dependency
- **Dual user system**: Admin and User types with different permissions
- **Token renewal** mechanism with expired token handling

#### Configuration Management
- **Environment-based configuration** using custom `CustomBaseSettings`
- **Multi-dotenv support**: Reads from `dotenvs/.env.{environment}` and `dotenvs/.env`
- **Settings validation** with Pydantic v1 compatibility

#### API Design
- **Versioned APIs** (v1) with clear route organization
- **Consistent response format** using `ListResult` for paginated responses
- **ORJSON responses** for performance optimization
- **Comprehensive error handling** with custom exception types

### Development Environment Setup
1. **Environment Variables**: Copy appropriate `.env` files to `dotenvs/` directory
2. **Database**: Configure MySQL connection in environment variables (uses aiomysql)
3. **Deployment Environment**: Set `DEPLOYMENT_ENVIRONMENT` (local/sandbox/qa/production)
4. **Dependencies**: Install with `poetry install` (project uses Poetry package management)

### Database Migrations
- **SQL migration files**: Located in `migrations/` directory with naming pattern `V{number}__{description}.sql`
- **Current migrations**: V1 (admins), V2 (users), V3 (notices)

### Code Style and Quality
- **Line length**: 120 characters (configured in `ruff.toml`)
- **Python version**: 3.13
- **Import sorting**: Using ruff's isort integration
- **Quote style**: Double quotes preferred
- **Async/await**: Extensively used throughout the application

### Testing Configuration
- **Test framework**: pytest with async support
- **Coverage reporting**: Configured in `pytest.ini` with term-missing report
- **Environment files**: Uses `dotenvs/.env` and `dotenvs/.env.test`
- **Test paths**: Tests should be in `tests/` directory
- **Async testing**: Configured with `asyncio_mode=auto` for automatic async test handling

### Key Tools and Dependencies
- **FastAPI 0.116.1**: Web framework with automatic OpenAPI documentation
- **SQLAlchemy 2.0.42**: ORM with async support
- **Pydantic 2.11.7**: Data validation and settings management
- **aiomysql 0.2.0**: Async MySQL connector
- **uvicorn 0.35.0**: ASGI server with uvloop for performance
- **Sentry SDK**: Error monitoring and logging
- **structlog**: Structured logging
- **PyJWT**: JWT token handling