"""This file contains tests for the LoggerMixin class."""

import os
from datetime import datetime
from pathlib import Path

from python_template.logger import LoggerMixin

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


def test_logger(test_class):
    """Function to test the LoggerMixin class."""
    logfile = test_class.logger_filename
    assert Path(logfile).is_file()
    test_class.logger.error(TEST_TEXT)
    # test_class.logger_handler.flush()
    with open(logfile, "r", encoding="utf8") as file:
        lines = file.readlines()
    assert TEST_TEXT in lines[0]


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
