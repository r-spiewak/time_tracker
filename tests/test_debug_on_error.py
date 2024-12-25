"""This file tests the module debug_on_error.py."""

import sys

from pytest_mock import MockerFixture


def test_info_interactive_mode(mocker: MockerFixture):
    """Test the `info` function when in interactive mode."""
    mock_stderr = mocker.patch("sys.stderr.isatty", return_value=False)
    mock_excepthook = mocker.patch("sys.__excepthook__")

    from python_template.debug_on_error import (  # pylint: disable=import-outside-toplevel
        info,
    )

    exc_type = ValueError
    exc_value = ValueError("Test error")
    exc_tb = None

    info(exc_type, exc_value, exc_tb)

    mock_stderr.assert_called_once()
    mock_excepthook.assert_called_once_with(exc_type, exc_value, exc_tb)


def test_info_non_interactive_mode(mocker: MockerFixture):
    """Test the `info` function when not in interactive mode."""
    mock_stderr = mocker.patch("sys.stderr.isatty", return_value=True)
    mock_traceback = mocker.patch("traceback.print_exception")
    mock_pdb = mocker.patch("pdb.post_mortem")

    from python_template.debug_on_error import (  # pylint: disable=import-outside-toplevel
        info,
    )

    exc_type = ValueError
    exc_value = ValueError("Test error")
    exc_tb = None

    info(exc_type, exc_value, exc_tb)

    mock_stderr.assert_called_once()
    mock_traceback.assert_called_once_with(exc_type, exc_value, exc_tb)
    mock_pdb.assert_called_once_with(exc_tb)


def test_sys_excepthook_set():
    """Test that sys.excepthook is set to the info function."""
    from python_template.debug_on_error import (  # pylint: disable=import-outside-toplevel
        info,
    )

    assert sys.excepthook == info  # pylint: disable=comparison-with-callable
