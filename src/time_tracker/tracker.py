"""This file contains the actual tracker."""

import csv
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path

from time_tracker.constants import (
    DEFAULT_FILENAME,
    DEFAULT_OUTPUT_DIR,
    HEADERS,
    ColumnHeaders,
)
from time_tracker.logger import LoggerMixin


class TimeTracker(LoggerMixin):
    """TimeTracker class."""

    class TrackerActions(Enum):
        """Enum class for valid TimeTracker actions."""

        REPORT = "report"
        STATUS = "status"
        TRACK = "track"

    def __init__(
        self,
        filename: str = DEFAULT_FILENAME,
        directory: str | None = None,
    ):
        """Initialize class."""
        super().__init__()
        dir_path = Path(directory) if directory else DEFAULT_OUTPUT_DIR
        self.filepath = dir_path / filename
        self.ensure_file_exists()
        self.actions = self.TrackerActions

    def ensure_file_exists(self):
        """Check if the file exists. If not, create it with default headers."""
        if not self.filepath.exists():
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with self.filepath.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(HEADERS)

    def get_all_entries(self) -> list[dict[str, str]]:
        """Get all entries in the file."""
        try:  # pylint: disable=too-many-try-statements
            with self.filepath.open("r", newline="") as f:
                return list(csv.DictReader(f))
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("⚠️ Failed to read CSV: %s", e)
            return []

    def get_last_entry(self) -> dict[str, str] | None:
        """Get last entry in file."""
        entries = self.get_all_entries()
        return entries[-1] if entries else None

    def safe_write_csv(self, rows: list[dict], mode: str = "w"):
        """Overwrites the CSV file with `rows`, ensuring safe CSV escaping.

        Args:
            rows (list[dict]): The rows to write.
            mode (str): The mode of file writing (e.g., "w" for write/overwrite,
                "a" for append). Defaults to "w".
        """
        append_char = "a"
        with open(self.filepath, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=HEADERS, quoting=csv.QUOTE_MINIMAL
            )
            if append_char not in mode:
                writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def track(self, task: str | None = None):
        """Track a timer (and maybe task).
        Start or stop timing, depending on current status."""
        now = datetime.now()
        last_entry = self.get_last_entry()

        if (
            last_entry
            and last_entry[  # pylint: disable=unsubscriptable-object
                ColumnHeaders.START.value
            ]
            and not last_entry[  # pylint: disable=unsubscriptable-object
                ColumnHeaders.END.value
            ]
        ):
            # Complete current entry:
            start_time = datetime.fromisoformat(
                last_entry[  # pylint: disable=unsubscriptable-object
                    ColumnHeaders.START.value
                ]
            )
            duration = (now - start_time).total_seconds()
            # with self.filepath.open("r", newline="") as f:
            #     lines = list(csv.reader(f))
            lines = self.get_all_entries()
            last_entry_task = last_entry.get(ColumnHeaders.TASK.value, "")
            task_entry = (
                last_entry_task + " " + task if task else last_entry_task
            )
            # Replace last row:
            lines[-1] = {
                ColumnHeaders.START.value: last_entry[  # pylint: disable=unsubscriptable-object
                    ColumnHeaders.START.value
                ],
                ColumnHeaders.END.value: now.isoformat(),
                ColumnHeaders.DURATION.value: f"{duration:.2f}",
                ColumnHeaders.TASK.value: task_entry,
            }
            # with self.filepath.open("w", newline="") as f:
            #     writer = csv.writer(f)
            #     writer.writerows(lines)
            self.safe_write_csv(lines)
            print(f"Stopped timer at {now}. Duration: {duration:.2f} seconds.")
        else:
            # Start new entry:
            new_entry = [
                {
                    ColumnHeaders.START.value: now.isoformat(),
                    ColumnHeaders.END.value: "",
                    ColumnHeaders.DURATION.value: "",
                    ColumnHeaders.TASK.value: task or "",
                }
            ]
            # with self.filepath.open("a", newline="") as f:
            #     writer = csv.writer(f)
            #     writer.writerow([now.isoformat(), "", "", task or ""])
            self.safe_write_csv(new_entry, mode="a")
            print(
                f"Started timer at {now}"
                + (f" for task: {task}" if task else ".")
            )

    def status(self):
        """Get status of currently tracked task, or no active timer."""
        last_entry = self.get_last_entry()
        if (
            last_entry
            and last_entry[  # pylint: disable=unsubscriptable-object
                ColumnHeaders.START.value
            ]
            and not last_entry[  # pylint: disable=unsubscriptable-object
                ColumnHeaders.END.value
            ]
        ):
            print(
                f"Currently tracking task: '{last_entry.get(ColumnHeaders.TASK.value, '')}'"
                f" since {last_entry[ColumnHeaders.START.value]}"  # pylint: disable=unsubscriptable-object
            )
        else:
            print("No active timer.")

    def report(
        self,
        filter_task: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ):
        """Output a report of time tracking."""
        entries = self.get_all_entries()
        # print(entries)
        totals: dict[str, float] = defaultdict(float)

        try:  # pylint: disable=too-many-try-statements
            start_dt = (
                datetime.strptime(start_date, "%Y-%m-%d").date()
                if start_date
                else None
            )
            end_dt = (
                datetime.strptime(end_date, "%Y-%m-%d").date()
                if end_date
                else None
            )
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")
            raise

        for entry in entries:
            task = entry.get(ColumnHeaders.TASK.value, "") or "Unspecified"
            duration = float(entry.get(ColumnHeaders.DURATION.value, "0") or 0)
            # print(duration)
            if ColumnHeaders.END.value in entry:  # Only finished entries.
                start_time = datetime.fromisoformat(
                    entry[ColumnHeaders.START.value]
                ).date()
                end_time = datetime.fromisoformat(
                    entry[ColumnHeaders.END.value]
                ).date()
                if start_dt and start_time < start_dt:
                    continue
                if end_dt and end_time > end_dt:
                    continue
                if filter_task and task != filter_task:
                    # print(f"Entry {entry} not in {filter_task}, skipping...")
                    continue
                totals[task] += duration
                # print(f"Current totals: {totals}")

        if not totals:
            print("No matching entries found.")
            return

        print("Time spent per task (in hours):")
        for task, seconds in totals.items():
            print(f"  {task}: {seconds / 3600:.2f} h")
        total_time = sum(totals.values())
        print(f"\nTotal time: {total_time / 3600:.2f} h")
