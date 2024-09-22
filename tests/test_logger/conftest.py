"""This file contains fixtures for use in pytest unit tests."""

import os

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
    os.remove(logfile)
