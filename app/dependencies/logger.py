import logging

import structlog


def setup_logger():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


log = structlog.get_logger()

sql_logger = logging.getLogger("sqlalchemy.engine")
sql_logger.setLevel(logging.INFO)


# structlog 핸들러 생성
class StructLogHandler(logging.Handler):
    def emit(self, record):
        log.debug(record.getMessage(), level=record.levelname)


logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[
        StructLogHandler(),
    ],
)
