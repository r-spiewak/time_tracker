"""This file contains tests for the TimeTracker class."""

import csv
import os
from datetime import datetime, timedelta

import pytest

from time_tracker.constants import ColumnHeaders

INVALID_DATE_FORMAT = "Invalid date format"
NO_ENTRIES = "No matching entries"


def test_start_tracking_creates_file(temp_tracker):
    """Test that starting tracking creates the file, if not present."""
    tracker = temp_tracker
    # assert not os.path.exists(tracker.filepath)  # File created in __init__; can't do this.
    test_task = "Test"
    tracker.track(task=test_task)
    assert os.path.exists(tracker.filepath)

    with open(tracker.filepath, encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0][ColumnHeaders.TASK.value] == test_task
        assert reader[0][ColumnHeaders.END.value] == ""


def test_stop_tracking_updates_entry(temp_tracker):
    """Test that stopping timer updates the entry in the file."""
    tracker = temp_tracker
    tracker.track(task="Work")
    tracker.track()

    with open(tracker.filepath, encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
        row = reader[0]
        assert row[ColumnHeaders.END.value] != ""
        assert float(row[ColumnHeaders.DURATION.value]) >= 0


# Test these methods too:
# ensure_file_exists
# get_all_entries
# get_last_entry


def test_report_with_filters(
    temp_tracker, capsys
):  # pylint: disable=too-many-locals
    """Test reporting with filters."""
    tracker = temp_tracker
    now = datetime.now()
    task_a = "A"
    task_b = "B"
    a_1_h = task_a + ": 1.00 h"
    a_2_h = task_a + ": 2.00 h"
    b_2_h = task_b + ": 2.00 h"

    # Add entries manually:
    entries = [
        # {  # This part is included in __init__.
        #     ColumnHeaders.START.value: ColumnHeaders.START.value,
        #     ColumnHeaders.END.value: ColumnHeaders.END.value,
        #     ColumnHeaders.TASK.value: ColumnHeaders.TASK.value,
        #     ColumnHeaders.DURATION.value: ColumnHeaders.DURATION.value,
        # },
        {
            ColumnHeaders.START.value: (now - timedelta(days=2)).isoformat(),
            ColumnHeaders.END.value: (
                now - timedelta(days=2, hours=-1)
            ).isoformat(),
            ColumnHeaders.TASK.value: task_a,
            ColumnHeaders.DURATION.value: 3600,
        },
        {
            ColumnHeaders.START.value: (now - timedelta(days=1)).isoformat(),
            ColumnHeaders.END.value: (
                now - timedelta(days=1, hours=-2)
            ).isoformat(),
            ColumnHeaders.TASK.value: task_b,
            ColumnHeaders.DURATION.value: 7200,
        },
        {
            ColumnHeaders.START.value: now.isoformat(),
            ColumnHeaders.END.value: (now + timedelta(hours=1)).isoformat(),
            ColumnHeaders.TASK.value: task_a,
            ColumnHeaders.DURATION.value: 3600,
        },
    ]
    for entry in entries:
        line = [
            entry[ColumnHeaders.START.value],
            entry[ColumnHeaders.END.value],
            entry[ColumnHeaders.DURATION.value],
            entry[ColumnHeaders.TASK.value],
        ]
        with tracker.filepath.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(line)

    # Report without filters:
    tracker.report()
    output = capsys.readouterr().out
    assert a_2_h in output
    assert b_2_h in output

    # Filter by task:
    tracker.report(filter_task=task_a)
    output = capsys.readouterr().out
    assert a_2_h in output
    assert task_b not in output

    # Filter by date:
    start = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    end = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    tracker.report(start_date=start, end_date=end)
    output = capsys.readouterr().out
    assert a_1_h in output
    assert b_2_h in output


def test_report_with_invalid_date(temp_tracker, capsys):
    """Test a report with invalid date format."""
    tracker = temp_tracker
    with pytest.raises(ValueError):
        tracker.report(start_date="invalid-date")
    captured = capsys.readouterr().out
    assert INVALID_DATE_FORMAT in captured


def test_no_entries_no_crash(temp_tracker, capsys):
    """Test that there is no crash in reporting if there are no entries."""
    tracker = temp_tracker
    tracker.report()
    assert NO_ENTRIES in capsys.readouterr().out
