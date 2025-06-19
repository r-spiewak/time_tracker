"""This file contains a pre-built logger that can be
easily incorporated into a project."""

import logging
import threading
import traceback
from datetime import datetime
from enum import IntEnum, auto
from pathlib import Path
from typing import cast

from python_template.config import settings

DEBUG_PRINTS = settings.debug_prints


class DebugCategory(IntEnum):
    """Debug category levels for logging, from least to
    most detailed.
    """

    @staticmethod
    def _generate_next_value_(  # pylint: disable=bad-dunder-name
        name,  # pylint: disable=unused-argument
        start,  # pylint: disable=unused-argument
        count,
        last_values,  # pylint: disable=unused-argument
    ):
        """Generate flexible insertion with 10-unit spacing
        between values."""
        return 10 * (count + 1)

    BASIC = auto()
    MODERATE = auto()
    DETAILED = auto()
    VERBOSE = auto()
    TRACE = auto()

    @classmethod
    def from_verbosity(cls, verbosity: int) -> "DebugCategory":
        """Convert a CLI verbosity to a DebugCategory.
        Automatically maps verbosity counts to enum values in order
        of increasing value.

        Args:
            verbosity (int): How much and what level of logging to include.
                Higher values indicates more logging.
        """
        # Get all categories sorted by their value:
        all_categories: list[DebugCategory] = sorted(cls)
        # Handle any verbosity level by clamping to valid range:
        if verbosity <= 0:
            return cls.BASIC
        # Clamp to available levels:
        index = min(verbosity - 1, len(all_categories) - 1)
        return all_categories[index]

    @classmethod
    def get_verbosity_help(cls) -> str:
        """Generate help text for verbosity levels."""
        categories = sorted(cls)
        lines = ["Verbosity levels:"]

        for i, category in enumerate(categories):
            v_flags = "-" + ("v" * (i + 1))
            lines.append(
                f"{v_flags}: {category.name.replace('_', ' ').title()}"
            )

        return "\n".join(lines)


class DebugCategoryFilter(
    logging.Filter
):  # pylint: disable=too-few-public-methods
    """Class for filtering debug logs of different levels."""

    def __init__(
        self,
        # max_category=0,
        max_category: DebugCategory = DebugCategory.BASIC,
    ):
        super().__init__()
        self.max_category = max_category

    def filter(self, record: logging.LogRecord):
        if not hasattr(record, "debug_category"):
            return True
        return record.debug_category <= self.max_category


class DebugCategoryNameFilter(
    logging.Filter
):  # pylint: disable=too-few-public-methods
    """Class for converting debug levels to a string for
    logger formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Default value if debug_category is not set
        record.debug_cat_name = ""

        if hasattr(record, "debug_category"):
            # Try to convert the numeric value back to enum name
            try:  # pylint: disable=too-many-try-statements
                cat_name = DebugCategory(record.debug_category).name
                # Format it nicely for the log output, e.g. [DETAILED]
                record.debug_cat_name = f"[{cat_name}]"
            except ValueError:
                # Fallback if the value doesn't match an enum
                record.debug_cat_name = f"[DEBUG{record.debug_category}]"

        # Always return True since this filter is just for adding info
        return True


class CategoryLogger(logging.Logger):
    """A subclass of logging.Logger that has debug categories."""

    debugLevels = DebugCategory

    def debug_with_category(
        self, msg: str, *args, category: int = 1, **kwargs
    ):
        """Log debug message with a category number (higher = more detailed).

        Args:
            msg (str): Message to log.
            *args: Any other positional arguments.
            category (int): Category of debug log. Higher number means
                more detailed logging. Defaults to 1.
            **kwargs: any other keyword arguments.
        """
        # Tell logging to look one frame higher in the stack
        # to get the correct caller information:
        kwargs["stacklevel"] = kwargs.get("stacklevel", 0) + 2

        # kwargs["extra"] = kwargs.get("extra", {})
        # if kwargs["extra"] is None:
        #     kwargs["extra"] = {}
        kwargs["extra"] = (
            kwargs["extra"] if isinstance(kwargs.get("extra"), dict) else {}
        )
        assert kwargs["extra"] is not None
        kwargs["extra"]["debug_category"] = category
        self.debug(msg, *args, **kwargs)


# class LoggerMixin (logging.getLoggerClass()):
# class LoggerMixin(type):
class LoggerMixin:  # pylint: disable=too-few-public-methods
    """A logger class that can be included in any project."""

    _debug_enabled = True
    _lock_logger = threading.Lock()  # Add a lock for thread safety.
    _loggers: dict = {}

    def __init__(  # pylint: disable=too-many-branches,too-many-statements
        self,
        logger_filename: str | Path | None = None,
        logger_format: str | None = None,
        verbosity: int = 0,
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
            verbosity (int): How much and what level of logging to include.
                Higher values indicates more logging. Defaults to 0
                (warnings).
            #args: Additional arguments to pass to super class.
        """
        # super().__init__(*args)
        with (
            LoggerMixin._lock_logger
        ):  # Acquire the lock before making changes.
            # Get call stack info:
            if hasattr(self, "logger"):
                if DEBUG_PRINTS:
                    print(f"{type(self).__name__} already has a logger.")
                return
            stack = traceback.extract_stack()
            caller = stack[-2]  # The frame that called this __init__.
            caller_info = f"{caller.filename}:{caller.lineno} in {caller.name}"
            self.logger_filename = logger_filename
            if self.logger_filename is not None:
                init_type = f"explicit filename: {self.logger_filename}"
                self.logger_filename = Path(self.logger_filename)
            else:
                self.logger_filename = Path(
                    f"logs/{datetime.now().strftime('%Y-%m-%d_%H.%M.%S.%f_%z')}"
                    f"_{self.__class__.__name__}_.log"
                )
                init_type = f"default filename: {str(self.logger_filename)}"
            self.logger_filename.parents[0].mkdir(parents=True, exist_ok=True)

            logger_key = str(self.logger_filename.absolute().resolve())
            if DEBUG_PRINTS:
                print(f"Using logger_key: {logger_key}")
                print(
                    f"Existing keys in _loggers: {list(LoggerMixin._loggers.keys())}"
                )
            if logger_key in LoggerMixin._loggers:
                self.logger: CategoryLogger = LoggerMixin._loggers[logger_key]
                if LoggerMixin._debug_enabled:
                    # print(f"Reusing logger {logger_key}")
                    self.logger.debug_with_category(
                        "LoggerMixin reusing logger with %s",
                        init_type,
                        category=self.logger.debugLevels.TRACE,
                    )
                    self.logger.debug_with_category(
                        "Called from: %s",
                        caller_info,
                        category=self.logger.debugLevels.TRACE,
                    )
                    self.logger.debug_with_category(
                        "Existing keys in _loggers: %s",
                        list(LoggerMixin._loggers.keys()),
                        category=self.logger.debugLevels.TRACE,
                    )
            else:
                # Use the custom logger class:
                logging.setLoggerClass(CategoryLogger)
                # logger_attribute_name = '_' + self.__name__ + '__logger'
                logger_name = ".".join(
                    [c.__name__ for c in self.__class__.__mro__[-2::-1]]
                )
                # setattr(self, logger_attribute_name, logging.getLogger(logger_name))
                # self.logger = cast(CategoryLogger, logging.getLogger(logger_name))
                self.logger = self.get_category_logger(logger_name)
                # Add the debug categories method to the logger:
                # self.logger.debug_cat = self.debug_with_category
                # Set logger level:
                self.verbosity = verbosity
                if verbosity == 0:
                    # self.logger.setLevel(logging.WARNING)
                    self.logger.setLevel(logging.INFO)
                else:
                    self.logger.setLevel(logging.DEBUG)
                    # self.debug_filter = DebugCategoryFilter(
                    #     max_category=verbosity
                    # )
                    self.max_category = DebugCategory.from_verbosity(verbosity)
                    self.debug_filter = DebugCategoryFilter(
                        max_category=self.max_category
                    )
                    self.logger.addFilter(self.debug_filter)
                # Add filter to convert category numbers to names for formatting
                cat_name_filter = DebugCategoryNameFilter()
                self.logger.addFilter(cat_name_filter)
                # Set the log file hander here:
                self.logger_handler = logging.FileHandler(self.logger_filename)
                if logger_format is not None:
                    self.logger_format = logger_format
                else:
                    self.logger_format = (
                        "%(asctime)s.%(msecs)d "
                        "%(levelname)-8s %(debug_cat_name)s"
                        "[%(pathname)s:%(lineno)d in %(funcName)s] "
                        "%(message)s"
                    )
                self.logger_handler.setFormatter(
                    logging.Formatter(self.logger_format)
                )
                self.logger.handlers = []
                self.logger.addHandler(self.logger_handler)
                # Store for future use:
                LoggerMixin._loggers[logger_key] = self.logger
                if LoggerMixin._debug_enabled:
                    # Log all the seup info:
                    self.logger.debug_with_category(
                        "LoggerMixin created new logger with %s",
                        init_type,
                        category=self.logger.debugLevels.TRACE,
                    )
                    self.logger.debug_with_category(
                        "Called from: %s",
                        caller_info,
                        category=self.logger.debugLevels.TRACE,
                    )
                    self.logger.debug_with_category(
                        "Existing keys in _loggers: %s",
                        list(LoggerMixin._loggers.keys()),
                        category=self.logger.debugLevels.TRACE,
                    )

    @staticmethod
    def get_category_logger(name: str) -> CategoryLogger:
        """Get a CategoryLogger instance with the given name.

        Args:
            name (str): Name of the logger file.

        Returns:
            CategoryLogger: Instance of the CategoryLogger class
                to use for logging.
        """
        return cast(CategoryLogger, logging.getLogger(name))

    # def __new__(cls, name: str, bases:tuple[type], dct: dict):
    #     """Method for instantiating new class instances."""
    #     return super().__new__(cls, name, bases, dct)
