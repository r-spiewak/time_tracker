"""This file contains tests for the LoggerMixin class."""

import os
from datetime import datetime
from pathlib import Path

from python_template.logger import LoggerMixin


def test_logger(test_class):
    """Function to test the LoggerMixin class."""
    logfile = test_class.logger_filename
    assert Path(logfile).is_file()
    test_text = "Some test text."
    test_class.logger.error(test_text)
    # test_class.logger_handler.flush()
    with open(logfile, "r", encoding="utf8") as file:
        lines = file.readlines()
    assert test_text in lines[0]

    # Test with custom logger_filename and logger_format:
    logger_filename = (
        f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}_Test.log"
    )
    logger_format = (
        "Extra stuff: %(asctime)s.%(msecs)d %(levelname)-8s "
        "[%(pathname)s:%(lineno)d in %(funcName)s] "
        "%(message)s"
    )

    class TestClass(LoggerMixin):  # pylint: disable=too-few-public-methods
        """Test class for LoggerMixin."""

        def __init__(
            self,
            logger_filename: str | Path | None = None,
            logger_format: str | None = None,
        ):
            """Initialize method using custom definitions.

            Args:
                logger_filename (str | Path | None):
                    See definition in logger.py.
                logger_format (str | None):
                    See definition in logger.py.
            """
            super().__init__(
                logger_filename=logger_filename,
                logger_format=logger_format,
            )

    custom_test_class = TestClass(
        logger_filename=logger_filename,
        logger_format=logger_format,
    )
    custom_logfile = custom_test_class.logger_filename
    assert Path(custom_logfile).is_file()
    custom_test_class.logger.error(test_text)
    with open(custom_logfile, "r", encoding="utf8") as file:
        new_lines = file.readlines()
    assert test_text in new_lines[0]
    custom_test_class.logger_handler.close()
    os.remove(custom_logfile)
