import os
import io
import click
import logging
from logging import LogRecord, _nameToLevel
from contextlib import redirect_stdout
from typing import Callable, List

log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
LOG_LEVEL = _nameToLevel.get(log_level, logging.INFO)


class MyFormatter:

    color_mapper = {
        logging.DEBUG: lambda msg: click.style(
            str(msg), fg="cyan"
        ),
        logging.INFO: lambda msg: click.style(
            str(msg), fg="green"
        ),
        logging.WARNING: lambda msg: click.style(
            str(msg), fg="yellow"
        ),
        logging.ERROR: lambda msg: click.style(
            str(msg), fg="red"
        ),
        logging.CRITICAL: lambda msg: click.style(
            str(msg), fg="bright_red"
        ),
    }

    def __init__(
            self,
            fmt: str = '[%(name)s - %(levelname)s] > %(message)s',
            datefmt: str = '%Y-%m-%D-%H:%M:%S',
            use_colors: bool = True
    ):
        self.formatter = logging.Formatter(
            fmt=fmt, datefmt=datefmt
        )
        self.base_fmt = fmt
        self.datefmt = datefmt
        self.use_colors = use_colors

    @property
    def fmt(self) -> str:
        return self.formatter._fmt

    def _change_fmt(self, fmt: str):
        self.formatter = logging.Formatter(fmt=fmt, datefmt=self.datefmt)

    def color_message(self, level_no: int, msg: str) -> str:
        """Color passed level and other string arguments."""
        func = self.color_mapper.get(level_no, lambda msg: click.style(
            str(msg), fg="green"
        ))
        return func(msg)
    
    def format(self, record: LogRecord) -> str:
        levelno = record.levelno
        self._change_fmt(self.color_message(levelno, self.base_fmt))
        if self.use_colors:
            return self.color_message(
                levelno, self.formatter.format(record)
            )
        return self.formatter.format(record)


# Create a global formatter
FORMATTER = MyFormatter(
    fmt="%(asctime)s \t [%(levelname)s] > %(message)s",
    datefmt='%Y-%m-%D-%H:%M:%S'
)

class BaseLogger:

    """
    Base logger class.
    """

    def __init__(self, name, level, formatter):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.formatter = formatter
        self.logger.propagate = False
        
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(self.formatter)
        self.logger.addHandler(ch)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def deprecation(self, message):
        message = f"DEPRECATION: {message}"
        self.logger.warning(message)

    def disable(self):
        self.logger.disabled = True

    def enable(self):
        self.logger.disabled = False

    def change_colors(self, level: List[str], color: List[str]) -> None:
        """Change colors of given level log."""
        for level, color in zip(level, color):
            self.formatter.color_mapper[_nameToLevel.get(level.upper())] = lambda level_name: click.style(
                str(level_name), fg=color
            )


# Global loggers dict
LOGGERS = {}


def get_logger(
        name: str,
) -> BaseLogger:

    """
    Wrapper method for creating loggers quickly.
    """

    global LOGGERS, LOG_LEVEL, FORMATTER

    if name in LOGGERS:
        return LOGGERS[name]
    else:
        _logger = BaseLogger(
            name, level=LOG_LEVEL, formatter=FORMATTER
        )
        LOGGERS[name] = _logger
        return _logger


def stdout_to_logger(logger: BaseLogger, func: Callable, *args) -> str:

    """
    Catch prints and move them to logger.
    """
    
    f = io.StringIO()
    with redirect_stdout(f):
        res = func(*args)
    
    o = f.getvalue()

    for line in o.splitlines():
        logger.info(line)

    return res

# We need a general logger for system messages
general_logger = get_logger('Universa')