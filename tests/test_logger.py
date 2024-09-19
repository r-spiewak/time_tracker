"""This file contains tests for the LoggerMixin class."""

from pathlib import Path


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
