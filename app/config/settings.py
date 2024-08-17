from os import PathLike
from typing import Any

from dotenv import dotenv_values
from orjson import loads
from pydantic.v1 import BaseSettings, Extra
from pydantic.v1.env_settings import SettingsSourceCallable


def _read_dotenv(env_file: str | PathLike | None, encoding: str | None) -> dict[str, str | None]:
    dotenv_vars = dotenv_values(env_file, encoding=encoding)
    return {k.lower(): v for k, v in dotenv_vars.items()}


def multiple_dotenv_settings_source(settings: BaseSettings) -> dict[str, Any]:
    env_files = settings.__config__.env_files  # type: ignore
    env_encoding = getattr(settings.__config__, "env_file_encoding", "utf-8")
    if not env_files:
        return {}

    if not isinstance(env_files, list | tuple):
        env_files = [env_files]

    dotenv_items = {}
    for env_file in reversed(env_files):
        for k, v in _read_dotenv(env_file, env_encoding).items():
            lower_key = k.lower()
            field = settings.__fields__.get(lower_key)
            if v is not None and field and field.is_complex():
                v = loads(v)

            dotenv_items[lower_key] = v
    return dotenv_items


class CustomBaseSettings(BaseSettings):
    class Config(BaseSettings.Config):
        allow_mutation = False
        extra = Extra.ignore

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return (
                init_settings,
                env_settings,
                multiple_dotenv_settings_source,
                file_secret_settings,
            )
