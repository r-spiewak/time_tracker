"""This file contains a pre-built logger that can be
easily incorporated into a project."""

import logging
from datetime import datetime
from pathlib import Path


# class LoggerMixin (logging.getLoggerClass()):
# class LoggerMixin(type):
class LoggerMixin:  # pylint: disable=too-few-public-methods
    """A logger class that can be included in any project."""

    def __init__(
        self,
        logger_filename: str | Path | None = None,
        logger_format: str | None = None,
        # *args,
    ):
        """Initialize the logger.

        Args:
            logger_filename (str | Path | None): Filename (and path)
                to which to write log. If None, writes to a file in
                the local logs directory (relative to the calling
                directory) with the filename given by the current
                timestamp and class name, with the estension ".log".
                Dafaults to None.
            logger_format (str | None): Format specifier for log messages.
                If None, defaults to 'timestamp level [file:lineno in func]
                message'. Defaults to None.
            #args: Additional arguments to pass to super class.
        """
        # super().__init__(*args)
        # logger_attribute_name = '_' + self.__name__ + '__logger'
        logger_name = ".".join(
            [c.__name__ for c in self.__class__.__mro__[-2::-1]]
        )
        # setattr(self, logger_attribute_name, logging.getLogger(logger_name))
        self.logger = logging.getLogger(logger_name)
        # Set logger level:
        self.logger.setLevel(logging.DEBUG)
        # Set the log file handler here:
        if logger_filename is not None:
            self.logger_filename = Path(logger_filename)
        else:
            self.logger_filename = Path(
                f"logs/{datetime.now().strftime('%Y-%m-%d_%H.%M.%S.%f_%z')}"
                f"_{self.__class__.__name__}_.log"
            )
        self.logger_filename.parents[0].mkdir(parents=True, exist_ok=True)
        self.logger_handler = logging.FileHandler(self.logger_filename)
        if logger_format is not None:
            self.logger_format = logger_format
        else:
            self.logger_format = (
                "%(asctime)s.%(msecs)d %(levelname)-8s "
                "[%(pathname)s:%(lineno)d in %(funcName)s] "
                "%(message)s"
            )
        self.logger_handler.setFormatter(logging.Formatter(self.logger_format))
        self.logger.addHandler(self.logger_handler)

    # def __new__(cls, name: str, bases:tuple[type], dct: dict):
    #     """Method for instantiating new class instances."""
    #     return super().__new__(cls, name, bases, dct)
