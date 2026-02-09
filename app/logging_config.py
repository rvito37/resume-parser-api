import logging
import sys
import contextvars

from app.config import LOG_LEVEL, ENVIRONMENT

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


def setup_logging():
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    if ENVIRONMENT == "production":
        fmt = '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","request_id":"%(request_id)s","msg":"%(message)s"}'
    else:
        fmt = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    logging.basicConfig(level=level, format=fmt, stream=sys.stdout, force=True)

    rid_filter = RequestIdFilter()
    for handler in logging.root.handlers:
        handler.addFilter(rid_filter)
