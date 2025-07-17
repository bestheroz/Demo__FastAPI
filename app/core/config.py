from functools import lru_cache
from os import getenv
from pathlib import Path

from pydantic import ValidationError

from app.core.settings import CustomBaseSettings

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


def get_dotenv_paths() -> list[Path]:
    dotenv_path = PACKAGE_ROOT / "dotenvs"
    env = getenv("DEPLOYMENT_ENVIRONMENT", "local")
    return [dotenv_path / f".env.{env}", dotenv_path / ".env"]


class Settings(CustomBaseSettings):
    # from environment variables
    deployment_environment: str

    # from.env files
    sentry_dsn: str
    jwt_secret_key: str
    db_name: str
    db_host: str
    db_username: str
    db_password: str
    db_port: str
    db_pool_size: int
    db_max_overflow: int
    db_pool_recycle: int

    class Config(CustomBaseSettings.Config):
        env_files = get_dotenv_paths()
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()  # type: ignore
    except ValidationError as e:
        missing_fields = [str(error["loc"][0]) for error in e.errors() if error.get("type") == "missing"]
        if missing_fields:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}") from e
        raise ValueError(f"Configuration validation failed: {e}") from e
