"""This file contains tests for the LoggerMixin class."""

import logging
import os
from datetime import datetime
from pathlib import Path

from python_template.logger import LoggerMixin
from python_template.logger.logger import DebugCategoryNameFilter

TEST_TEXT = "Some test text."


class CustomTestClass(LoggerMixin):  # pylint: disable=too-few-public-methods
    """Test class for LoggerMixin."""

    def __init__(
        self,
        logger_filename: str | Path | None = None,
        logger_format: str | None = None,
        verbosity: int = 0,
    ):
        """Initialize method using custom definitions.

        Args:
            logger_filename (str | Path | None):
                See definition in logger.py.
            logger_format (str | None):
                See definition in logger.py.
            verbosity (int):
                See definition in logger.py.
        """
        super().__init__(
            logger_filename=logger_filename,
            logger_format=logger_format,
            verbosity=verbosity,
        )
        # super goes through this class's MRO (method resultion order).
        # An alternative would be to directly use LoggerMixin.__init__().


def test_logger(capsys, test_class):
    """Function to test the LoggerMixin class."""
    logfile = test_class.logger_filename
    assert Path(logfile).is_file()
    test_class.logger.error(TEST_TEXT)
    # test_class.logger_handler.flush()
    with open(logfile, "r", encoding="utf8") as file:
        lines = file.readlines()
    assert TEST_TEXT in lines[0]
    out, _ = capsys.readouterr()
    using_key_text = "Using logger_key:"
    existing_key_text = "Existing keys in _loggers:"
    assert using_key_text in out
    assert existing_key_text in out


def test_custom_logger():
    """Function to test LoggerMixin class with custom inputs."""
    # Test with custom logger_filename and logger_format:
    logger_filename = (
        f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}_Test.log"
    )
    logger_format = (
        "Extra stuff: %(asctime)s.%(msecs)d %(levelname)-8s "
        "[%(pathname)s:%(lineno)d in %(funcName)s] "
        "%(message)s"
    )

    custom_test_class = CustomTestClass(
        logger_filename=logger_filename,
        logger_format=logger_format,
        verbosity=5,
    )
    custom_logfile = custom_test_class.logger_filename
    assert Path(custom_logfile).is_file()
    custom_test_class.logger.error(TEST_TEXT)
    with open(custom_logfile, "r", encoding="utf8") as file:
        new_lines = file.readlines()
    assert TEST_TEXT in new_lines[3]
    custom_test_class.logger_handler.close()
    os.remove(custom_logfile)


def test_existing_logger(test_class):
    """Test that an existing logger is used when given the same logger_filename."""
    logger_filename = test_class.logger_filename
    custom_test_class = CustomTestClass(
        logger_filename=logger_filename,
    )
    assert custom_test_class.logger_filename == logger_filename
    assert custom_test_class.logger == test_class.logger


def test_custom_logger_level_clamping():
    """Function to test that verbosity levels <=0 will get level BASIC."""
    custom_test_class = CustomTestClass(
        verbosity=-1,
    )
    assert (
        custom_test_class.max_category
        == custom_test_class.logger.debugLevels.BASIC
    )
    custom_logfile = custom_test_class.logger_filename
    os.remove(custom_logfile)


def test_invalid_debug_category(test_class):
    """Function to test that invalid debug cateogry doesn't print."""
    logfile = test_class.logger_filename
    test_class.logger.debug_with_category(TEST_TEXT, category="random")
    with open(logfile, "r", encoding="utf8") as file:
        lines = file.readlines()
    assert len(lines) == 0


def test_debug_category_name_filter_invalid_enum_value():
    """Test the DebugCategoryFilter with an invalid enum value."""
    cat_num = 999
    cat_name = f"[DEBUG{cat_num}]"
    # Create a dummy log record:
    record = logging.LogRecord(
        name="test_logger",
        level=logging.DEBUG,
        pathname="test_path",
        lineno=42,
        msg="Test log message",
        args=(),
        exc_info=None,
    )

    # Assign a debug_category that is invalid for the DebugCategory enum:
    record.debug_category = cat_num

    # Apply the filter:
    debug_filter = DebugCategoryNameFilter()
    result = debug_filter.filter(record)

    # Assertions:
    assert result is True
    assert hasattr(record, "debug_cat_name")
    assert record.debug_cat_name == cat_name  # pylint: disable=no-member


def test_category_logger_kwargs_extra_none():
    """Tests that if the 'extra' kwarg is explicitly passed as None that
    it still appropriately gets set to a dict."""
    custom_test_class = CustomTestClass(
        verbosity=5,
    )
    custom_test_class.logger.debug_with_category(
        TEST_TEXT,
        category=custom_test_class.logger.debugLevels.BASIC,
        extra=None,
    )
    logfile = custom_test_class.logger_filename
    with open(logfile, "r", encoding="utf8") as file:
        lines = file.readlines()
    assert len(lines) == 1
    assert TEST_TEXT in lines[0]
    os.remove(logfile)
