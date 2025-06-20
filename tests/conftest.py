"""This file contains fic=xtures for pytest for the TimeTracker class."""

import datetime
import os
import shutil
import tempfile

import pytest

from time_tracker.tracker import TimeTracker


@pytest.fixture
def mock_tracker(mocker):
    """A fixture for a mock tracker."""
    mock = mocker.Mock()
    mock.actions = TimeTracker.TrackerActions
    mock.track = mocker.Mock()
    mock.status = mocker.Mock()
    mock.report = mocker.Mock()
    mock.generate_invoice = mocker.Mock()
    mock.init_config = mocker.Mock()

    # Patch the TimeTracker class to return this mock
    mocker.patch("time_tracker.run.TimeTracker", return_value=mock)

    return mock


@pytest.fixture
def mock_tracker_logger(mocker):
    """A fixture for a mock logger __init__."""
    logger_mock = mocker.Mock()
    mocker.patch(
        "time_tracker.tracker.LoggerMixin.__init__", return_value=logger_mock
    )
    return logger_mock


@pytest.fixture
def temp_tracker(
    mock_tracker_logger,
):  # pylint: disable=redefined-outer-name,unused-argument
    """A fixture tracker object for testing."""
    temp_dir = tempfile.mkdtemp()
    logger_filename = (
        f"{temp_dir}/"
        f"logs/{datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S.%f_%z')}"
        f"_{type(TimeTracker).__name__}_.log"
    )
    tracker = TimeTracker(
        filename="test.csv",
        directory=temp_dir,
        logger_filename=logger_filename,
    )
    logfile = (
        tracker.logger_filename
        if hasattr(tracker, "logger_filename")
        else None
    )
    yield tracker
    if (
        hasattr(tracker, "logger")
        and hasattr(tracker.logger, "handlers")
        and hasattr(tracker.logger.handlers, "__iter__")
    ):
        for handler in tracker.logger.handlers:
            handler.close()
    if logfile and os.path.exists(logfile):
        os.remove(logfile)
    shutil.rmtree(temp_dir)
