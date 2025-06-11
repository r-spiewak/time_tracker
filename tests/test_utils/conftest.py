"""This file contains fixtures for use in pytest unit tests."""

import gc
import os
import shutil
import stat
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create and clean up a temporary directory for tests."""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path

    # Try to clean up lingering file handles
    gc.collect()

    def onerror(func, path, exc_info):  # pylint: disable=unused-argument
        """Handle permission errors on Windows."""

        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
        try:
            func(path)
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # Last resort: ignore if still fails

    shutil.rmtree(dir_path, onerror=onerror)
