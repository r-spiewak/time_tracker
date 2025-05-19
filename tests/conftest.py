"""This file contains fic=xtures for pytest for the TimeTracker class."""

import shutil
import tempfile

import pytest

from time_tracker.tracker import TimeTracker


@pytest.fixture
def temp_tracker():
    """A fixture tracker object for testing."""
    temp_dir = tempfile.mkdtemp()
    tracker = TimeTracker(
        filename="test.csv",
        directory=temp_dir,
    )
    yield tracker
    shutil.rmtree(temp_dir)
