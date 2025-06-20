"""This file contains tests for the TimeTracker class."""

import csv
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import CalledProcessError

import pytest

from time_tracker import TimeTracker
from time_tracker.constants import HEADERS, ColumnHeaders

INVALID_DATE_FORMAT = "Invalid date format"
NO_ENTRIES = "No matching entries"


def manual_entries(tracker):
    """Create manual entries in a tracker."""
    now = datetime.now()
    task_a = "A"
    task_b = "B"
    a_1_h = task_a + ": 1.00 h"
    a_2_h = task_a + ": 2.00 h"
    b_1_h = task_b + ": 1.00 h"
    b_2_h = task_b + ": 2.00 h"
    b_3_h = task_b + ": 3.00 h"

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
        {
            ColumnHeaders.START.value: (now + timedelta(days=2)).isoformat(),
            ColumnHeaders.END.value: (
                now + timedelta(days=2, hours=1)
            ).isoformat(),
            ColumnHeaders.TASK.value: task_b,
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
    return {
        "entries": entries,
        "time": now,
        "tasks": {
            "task_a": task_a,
            "task_b": task_b,
        },
        "durations": {
            "a_1_h": a_1_h,
            "a_2_h": a_2_h,
            "b_1_h": b_1_h,
            "b_2_h": b_2_h,
            "b_3_h": b_3_h,
        },
    }


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


def test_ensure_file_exists(temp_tracker):
    """Tests the ensure_file_exists method."""
    tracker = temp_tracker
    assert os.path.exists(tracker.filepath)
    os.unlink(tracker.filepath)
    assert not os.path.exists(tracker.filepath)
    tracker.ensure_file_exists()
    assert os.path.exists(tracker.filepath)

    with open(tracker.filepath, "r", encoding="utf-8", newline="") as f:
        lines = f.readlines()
    assert len(lines) == 1
    assert lines[0] == ",".join(HEADERS) + "\r\n"


def test_get_all_entries(temp_tracker, monkeypatch, mocker):
    """Tests the get_all_entries method."""
    tracker = temp_tracker

    manual_dict = manual_entries(tracker)
    entries = manual_dict["entries"]
    # all_entries = []
    # for entry in entries:
    #     all_entries.append(
    #         [
    #             entry[ColumnHeaders.START.value],
    #             entry[ColumnHeaders.END.value],
    #             entry[ColumnHeaders.DURATION.value],
    #             entry[ColumnHeaders.TASK.value],
    #         ]
    #     )

    read_entries = tracker.get_all_entries()
    for read_entry, entry in zip(read_entries, entries):
        for key in entry.keys():
            assert read_entry[key] == str(entry[key])

    bad_csv_filename = "bad.csv"
    bad_csv_filepath = tracker.filepath.parent / bad_csv_filename
    with open(str(bad_csv_filepath), "w", encoding="utf8") as bad:
        bad.writelines(["col1", "1,2"])
    tracker.filepath = bad_csv_filepath
    read_entries = tracker.get_all_entries()
    assert read_entries == []

    def mock_open(*args, **kwargs):
        """Mock open function returning an error."""
        raise OSError("Simulated file read error.")

    monkeypatch.setattr(Path, "open", mock_open)
    # mock_logger = mocker.patch(tracker.logger)
    mock_logger = mocker.Mock()
    tracker.logger = mock_logger
    read_entries = tracker.get_all_entries()
    assert read_entries == []
    # mock_logger.error.assert_called_once()


def test_get_last_entry(temp_tracker):
    """Tests the get_last_entry method."""
    tracker = temp_tracker

    manual_dict = manual_entries(tracker)
    entries = manual_dict["entries"]
    # last_entry = [
    #     entries[-1][ColumnHeaders.START.value],
    #     entries[-1][ColumnHeaders.END.value],
    #     entries[-1][ColumnHeaders.DURATION.value],
    #     entries[-1][ColumnHeaders.TASK.value],
    # ]

    entry = tracker.get_last_entry()
    for key in entries[  # pylint: disable=consider-iterating-dictionary
        -1
    ].keys():
        assert entry[key] == str(entries[-1][key])


def test_report_with_filters(
    temp_tracker, capsys
):  # pylint: disable=too-many-locals
    """Test reporting with filters."""
    tracker = temp_tracker

    manual_dict = manual_entries(tracker)
    now = manual_dict["time"]
    task_a = manual_dict["tasks"]["task_a"]
    task_b = manual_dict["tasks"]["task_b"]
    a_1_h = manual_dict["durations"]["a_1_h"]
    a_2_h = manual_dict["durations"]["a_2_h"]
    # b_1_h = manual_dict["durations"]["b_1_h"]
    b_2_h = manual_dict["durations"]["b_2_h"]
    b_3_h = manual_dict["durations"]["b_3_h"]

    # Report without filters:
    tracker.report()
    output = capsys.readouterr().out
    assert a_2_h in output
    assert b_3_h in output

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


def test_client_not_in_client_config(capsys):
    """Tests when client isn't in client_config."""
    temp_dir = tempfile.mkdtemp()
    client = "client-1"
    msg = f"Client {client} not in client config."
    filename = f"{client}.csv"
    logger_filename = (
        f"{temp_dir}/"
        f"logs/{datetime.now().strftime('%Y-%m-%d_%H.%M.%S.%f_%z')}"
        f"_{type(TimeTracker).__name__}_.log"
    )
    tracker = TimeTracker(
        directory=temp_dir, client=client, logger_filename=logger_filename
    )
    assert msg in capsys.readouterr().out
    assert tracker.filepath == Path(temp_dir) / filename


def test_generate_invoice(
    tmp_path, mocker, mock_tracker_logger
):  # pylint: disable=unused-argument,too-many-locals
    """Test the generate_invoice method."""
    two = 2
    # Setup paths:
    tex_template = tmp_path / "invoice_template.tex"
    tex_template.write_text("Invoice ((( total )))")

    mocker.patch("time_tracker.tracker.DEFAULT_INVOICE_DIR", tmp_path)
    mocker.patch("time_tracker.tracker.DEFAULT_INVOICE_TEMPLATE", tex_template)
    mocker.patch("time_tracker.tracker.SAMPLE_INVOICE_TEMPLATE", tex_template)

    mocker.patch(
        "time_tracker.tracker.get_next_invoice_number", return_value=999
    )
    mocker.patch(
        "time_tracker.tracker.prepare_logo_for_latex", return_value="logo.pdf"
    )

    # Tracker instance with mocks:
    tracker = TimeTracker()
    tracker.client = "test_client"
    tracker.generate_report = mocker.Mock(
        return_value=(
            {"dev": 3600},  # 1 hour
            [datetime(2023, 1, 1), datetime(2023, 1, 2)],
        )
    )
    tracker.client_config = mocker.Mock()
    tracker.client_config.clients = {
        "test_client": mocker.Mock(rate=150, name="Test Co.")
    }
    tracker.me = mocker.Mock(logo_path="logo.svg")

    mock_logger = mocker.Mock()
    tracker.logger = mock_logger

    mock_run = mocker.patch("time_tracker.tracker.subprocess.run")

    # Run invoice generator:
    tracker.generate_invoice()
    tex_test_filename = tmp_path / (
        f"{datetime.today().strftime('%Y_%m_%d')}-"
        f"{tracker.client}_invoice.tex"
    )

    # Check output .tex written:
    tex_out = list(tmp_path.glob("*.tex"))
    assert len(tex_out) == two
    assert tex_template in tex_out
    assert tex_test_filename in tex_out
    assert tex_test_filename.read_text().startswith("Invoice")

    # Check subprocess and logger call:
    mock_run.assert_called_once()
    mock_logger.info.assert_called_once_with(
        f"✅ Invoice created: {tmp_path / tex_out[0].with_suffix('.pdf').name}"
    )

    # Test when filename is given:
    tex_filename = tmp_path / "invoice_filename.tex"
    tracker.generate_invoice(invoice_filename=tex_filename)
    # Check output .tex written:
    tex_out = list(tmp_path.glob("*.tex"))
    assert tex_filename in tex_out
    assert tex_filename.read_text().startswith("Invoice")

    # Test when subprocess gives an error:
    retcode = 1
    command = "madeup"
    output = "output"
    err = "err"
    error = CalledProcessError(
        returncode=retcode,
        cmd=command,
        output=output,
        stderr=err,
    )

    def mock_error(*args, **kwargs):  # pylint: disable=unused-argument
        """Mock error"""
        raise error

    mocker.patch("time_tracker.tracker.subprocess.run", mock_error)
    tracker.generate_invoice(invoice_filename=tex_filename)
    assert (
        mocker.call("❌ Failed to compile LaTeX invoice: %s", error)
        in mock_logger.warning.call_args_list
    )
    assert (
        mocker.call("📄 STDOUT:\n%s", output)
        in mock_logger.warning.call_args_list
    )
    assert (
        mocker.call("🐞 STDERR:\n%s", err)
        in mock_logger.warning.call_args_list
    )


def test_init_config(
    tmp_path, mocker, mock_tracker_logger
):  # pylint: disable=unused-argument
    """Test the init_config method."""
    empty_dict_str = "{}"
    template = "TEMPLATE"
    # Create dummy sample files:
    sample_client = tmp_path / "sample_client.json"
    sample_client.write_text(empty_dict_str)
    sample_template = tmp_path / "sample_template.tex"
    sample_template.write_text(template)
    sample_me = tmp_path / "sample_me.json"
    sample_me.write_text(empty_dict_str)
    sample_invoice_state = tmp_path / "sample_invoice_state.json"
    sample_invoice_state.write_text(empty_dict_str)

    dest_client = tmp_path / "client.json"
    dest_template = tmp_path / "template.tex"
    dest_me = tmp_path / "me.json"
    dest_state = tmp_path / "invoice_state.json"

    # with mocker.patch.multiple(
    #     "time_tracker.tracker",
    #     SAMPLE_CLIENT_CONFIG_FILE=sample_client,
    #     SAMPLE_INVOICE_TEMPLATE=sample_template,
    #     SAMPLE_ME_CONFIG_FILE=sample_me,
    #     SAMPLE_INVOICE_STATE_CONFIG_FILE=sample_invoice_state,
    #     DEFAULT_CLIENT_CONFIG_FILE=dest_client,
    #     DEFAULT_INVOICE_TEMPLATE=dest_template,
    #     DEFAULT_ME_CONFIG_FILE=dest_me,
    #     DEFAULT_INVOICE_STATE_CONFIG_FILE=dest_state,
    # ):
    mocker.patch(
        "time_tracker.tracker.SAMPLE_CLIENT_CONFIG_FILE", sample_client
    )
    mocker.patch(
        "time_tracker.tracker.SAMPLE_INVOICE_TEMPLATE", sample_template
    )
    mocker.patch("time_tracker.tracker.SAMPLE_ME_CONFIG_FILE", sample_me)
    mocker.patch(
        "time_tracker.tracker.SAMPLE_INVOICE_STATE_CONFIG_FILE",
        sample_invoice_state,
    )
    mocker.patch(
        "time_tracker.tracker.DEFAULT_CLIENT_CONFIG_FILE", dest_client
    )
    mocker.patch(
        "time_tracker.tracker.DEFAULT_INVOICE_TEMPLATE", dest_template
    )
    mocker.patch("time_tracker.tracker.DEFAULT_ME_CONFIG_FILE", dest_me)
    mocker.patch(
        "time_tracker.tracker.DEFAULT_INVOICE_STATE_CONFIG_FILE", dest_state
    )
    from time_tracker.tracker import (  # pylint: disable=import-outside-toplevel,reimported,redefined-outer-name
        TimeTracker,
    )

    TimeTracker.init_config()

    assert dest_client.read_text() == empty_dict_str
    assert dest_template.read_text() == template
    assert dest_me.read_text() == empty_dict_str
    assert dest_state.read_text() == empty_dict_str
