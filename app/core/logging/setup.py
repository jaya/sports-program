import logging
import sys

import structlog
from structlog.stdlib import LoggerFactory, ProcessorFormatter

from app.core.config import settings

SENSITIVE_FIELDS = {
    "user_id",
    "slack_id",
    "team_id",
    "enterprise_id",
    "state",
}


def setup_logging():
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    processors, renderer, log_level = get_environment_logging_config(shared_processors)

    structlog.configure(
        processors=processors
        + [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    configure_std_logging_and_uvicorn(processors, renderer, log_level)


def get_environment_logging_config(processors: list):
    if settings.DEBUG:
        processors.append(
            structlog.processors.CallsiteParameterAdder(
                {structlog.processors.CallsiteParameter.LINENO}
            )
        )
        return processors, structlog.dev.ConsoleRenderer(), logging.DEBUG

    processors.insert(0, obfuscate_sensitive_fields)
    return processors, structlog.processors.JSONRenderer(), logging.INFO


def configure_std_logging_and_uvicorn(
    processors: list,
    renderer,
    log_level: int,
) -> None:
    handler = logging.StreamHandler(sys.stdout)

    formatter = ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=processors,
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True


def obfuscate_sensitive_fields(logger, method_name, event_dict):
    for field in SENSITIVE_FIELDS:
        value = event_dict.get(field)
        if value:
            event_dict[field] = obfuscate_data(value)
    return event_dict


def obfuscate_data(value: str, prefix: int = 3, suffix: int = 2) -> str:
    value = str(value)
    if len(value) <= prefix + suffix:
        return "***"
    return f"{value[:prefix]}***{value[-suffix:]}"
