"""This file contains fixtures for use in pytest unit tests."""

import os
from pathlib import Path

import pytest

from python_template.logger import LoggerMixin


@pytest.fixture
def test_class():
    """Fixture to create a test class using the LoggerMixin class."""

    class TestClass(LoggerMixin):  # pylint: disable=too-few-public-methods
        """Test class using the LoggerMixin class."""

    test_class_instance = TestClass()
    logfile = test_class_instance.logger_filename
    yield test_class_instance
    test_class_instance.logger_handler.close()
    if os.path.exists(logfile):
        os.remove(logfile)


@pytest.fixture
def create_custom_test_class():
    """Factory fixture to create a test class with custom arguments to the
    LoggerMixin class and clean up afterwards"""
    instances = []

    def _create_custom_test_class(
        logger_filename=None,
        logger_format=None,
        verbosity=0,
    ):
        class CustomTestClass(
            LoggerMixin
        ):  # pylint: disable=too-few-public-methods
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

        instance = CustomTestClass(
            logger_filename=logger_filename,
            logger_format=logger_format,
            verbosity=verbosity,
        )
        instances.append(instance)
        return instance

    yield _create_custom_test_class
    for instance in instances:
        logfile = instance.logger_filename
        if os.path.exists(logfile):
            os.remove(logfile)
