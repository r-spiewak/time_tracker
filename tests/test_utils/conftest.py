"""This file contains fixtures for use in pytest unit tests."""

import gc
import os
import shutil
import stat
import tempfile
from pathlib import Path

import pytest

from python_template.utils.split_args_for_inits import (
    split_args_for_inits_strict_kwargs,
)


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


@pytest.fixture
def split_args():
    """Wrapper fixture for split_args_for_inits_strict_kwargs."""
    # from split_module import split_args_for_inits_strict_kwargs
    return lambda *args, **kwargs: split_args_for_inits_strict_kwargs(  # pylint:disable=unnecessary-lambda
        *args, **kwargs
    )


@pytest.fixture
def class_wrapper():
    """Wrapper fixture for classes."""

    def _class_wrapper(base_class):
        """Construct a wrapper class around base_class."""

        class ClassWrapper(
            base_class
        ):  # pylint: disable=too-few-public-methods
            """A wrapper class around base_class."""

        return ClassWrapper

    return _class_wrapper
