import logging

import structlog


def setup_logger():
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


log = structlog.get_logger()

sql_logger = logging.getLogger("sqlalchemy.engine")
sql_logger.setLevel(logging.INFO)


class StructLogHandler(logging.Handler):
    """stdlib 로그를 structlog으로 라우팅하는 핸들러"""

    def emit(self, record: logging.LogRecord) -> None:
        level = record.levelname.lower()
        logger = structlog.get_logger()
        getattr(logger, level, logger.info)(record.getMessage(), logger_name=record.name)


logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[
        StructLogHandler(),
    ],
)
