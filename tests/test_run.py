"""Test the CLI app."""

import os
import shutil
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from time_tracker.run import app
from time_tracker.tracker import TimeTracker

CURRENTLY_TRACKING = "Currently tracking task:"
DURATION = "Duration:"
NO_ACIVE_TIMER = "No active timer."
STARTED_TIMER = "Started timer"
STOPPED_TIMER = "Stopped timer"
VERBOSITY_2 = "Verbosity: 2"
VERBOSITY_3 = "Verbosity: 3"

runner = CliRunner()


def create_temp_env():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    return temp_dir


def test_app(capsys, mock_tracker_logger):  # pylint: disable=unused-argument
    """Test the cli app invocation."""
    temp_dir = create_temp_env()
    test_file = "cli_test.csv"
    file_path = os.path.join(temp_dir, test_file)
    result = runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    with capsys.disabled():
        print("stdout:")
        print(result.stdout)
        # print("stderr:")
        # print(result.stderr)
        # Need to capture stderr separately.
        # Otherwise it's bundled in with stdout.
    assert result.exit_code == 0
    assert Path(file_path).exists()


def test_tracking(mock_tracker_logger):  # pylint: disable=unused-argument
    """Test tracking functionality."""
    temp_dir = create_temp_env()
    test_file = "cli_test.csv"

    # Start tracking:
    result = runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    assert result.exit_code == 0
    assert STARTED_TIMER in result.output

    # Stop tracking:
    result = runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    assert result.exit_code == 0
    assert STOPPED_TIMER in result.output
    assert DURATION in result.output

    shutil.rmtree(temp_dir)


def test_status(mock_tracker_logger):  # pylint: disable=unused-argument
    """Test the 'status' feature."""
    temp_dir = create_temp_env()
    test_file = "cli_test.csv"

    # Start tracking:
    result = runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    assert result.exit_code == 0
    # Check status:
    result = runner.invoke(
        app,
        [
            "--action",
            "status",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    assert result.exit_code == 0
    assert CURRENTLY_TRACKING in result.output

    # Stop tracking:
    result = runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    assert result.exit_code == 0
    # Check status:
    result = runner.invoke(
        app,
        [
            "--action",
            "status",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    assert result.exit_code == 0
    assert NO_ACIVE_TIMER in result.output

    shutil.rmtree(temp_dir)


def test_cli_report_with_task_filter(  # pylint: disable=unused-argument
    mock_tracker_logger,
):
    """Test the 'report' feature."""
    temp_dir = create_temp_env()
    test_file = "report_test.csv"

    task_a = "A"
    task_b = "B"
    time_spent = "Time spent"

    # Start and stop a few sessions:
    runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
            "--task",
            task_a,
        ],
    )
    runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
            "--task",
            task_b,
        ],
    )
    runner.invoke(
        app,
        [
            "--action",
            "track",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )

    # Filter report:
    result = runner.invoke(
        app,
        [
            "--action",
            "report",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
            "--task",
            task_a,
        ],
    )
    assert result.exit_code == 0
    assert time_spent in result.output
    assert task_a in result.output
    assert task_b not in result.output

    shutil.rmtree(temp_dir)


def test_cli_invalid_date_filter(  # pylint: disable=unused-argument
    mock_tracker_logger,
):
    """Test for invalid date format."""
    temp_dir = create_temp_env()
    test_file = "invalid_date.csv"
    invalid_date = "Invalid date format"

    result = runner.invoke(
        app,
        [
            "--action",
            "report",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
            "--start-date",
            "not-a-date",
        ],
    )
    assert result.exit_code != 0
    assert invalid_date in result.output

    shutil.rmtree(temp_dir)


def test_cli_unknown_action(
    mock_tracker_logger,
):  # pylint: disable=unused-argument
    """Test the CLI when given an unknown action."""
    temp_dir = create_temp_env()
    test_file = "invalid_date.csv"

    result = runner.invoke(
        app,
        [
            "--action",
            "bob",
            "--filename",
            test_file,
            "--directory",
            temp_dir,
        ],
    )
    assert result.exit_code == 0
    assert STARTED_TIMER in result.output

    shutil.rmtree(temp_dir)


def test_verbosity_flag_changes_state(  # pylint: disable=unused-argument
    mock_tracker_logger,
):
    """Test that verbosity flag updates the state dictionary."""
    result = runner.invoke(app, ["--action", "status", "-vv"])
    assert result.exit_code == 0
    assert VERBOSITY_2 in result.output


def test_run_invokes_app(mocker):
    """Test that the run function invokes app."""
    # mock_app_call = mocker.patch.object(run_module.app, "__call__")
    # run_module.run()
    mock_app_call = mocker.Mock()
    mocker.patch("time_tracker.run.app", mock_app_call)
    from time_tracker.run import run  # pylint: disable=import-outside-toplevel

    run()
    mock_app_call.assert_called_once()


def test_main_actions(mocker):
    """Test the main function calls based on the action input."""
    mock_tracker = mocker.Mock()
    mock_tracker.actions = TimeTracker.TrackerActions
    mock_tracker.track = mocker.Mock()
    mock_tracker.status = mocker.Mock()
    mock_tracker.report = mocker.Mock()
    mock_tracker.generate_invoice = mocker.Mock()
    mock_tracker.init_config = mocker.Mock()
    mocker.patch("time_tracker.run.TimeTracker", return_value=mock_tracker)
    from time_tracker.run import (  # pylint: disable=import-outside-toplevel
        main,
    )

    main()
    mock_tracker.track.assert_called_once()
    main(action=mock_tracker.actions.STATUS.value)
    mock_tracker.status.assert_called_once()
    main(action=mock_tracker.actions.REPORT.value)
    mock_tracker.report.assert_called_once()
    main(action=mock_tracker.actions.INVOICE.value)
    mock_tracker.generate_invoice.assert_called_once()
    main(action=mock_tracker.actions.INNITIALIZE.value)
    mock_tracker.init_config.assert_called_once()
