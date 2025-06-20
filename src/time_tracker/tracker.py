"""This file contains the actual tracker."""

import csv
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from time_tracker.constants import (
    DEFAULT_CLIENT,
    DEFAULT_CLIENT_CONFIG_FILE,
    DEFAULT_INVOICE_DIR,
    DEFAULT_INVOICE_STATE_CONFIG_FILE,
    DEFAULT_INVOICE_TEMPLATE,
    DEFAULT_ME_CONFIG_FILE,
    DEFAULT_OUTPUT_DIR,
    HEADERS,
    SAMPLE_CLIENT_CONFIG_FILE,
    SAMPLE_INVOICE_STATE_CONFIG_FILE,
    SAMPLE_INVOICE_TEMPLATE,
    SAMPLE_ME_CONFIG_FILE,
    ColumnHeaders,
)
from time_tracker.logger import LoggerMixin

from .config import (
    get_next_invoice_number,
    load_client_config,
    load_me_config,
    prepare_logo_for_latex,
)


class TimeTracker(LoggerMixin):
    """TimeTracker class."""

    class TrackerActions(Enum):
        """Enum class for valid TimeTracker actions."""

        INNITIALIZE = "initialize"
        INVOICE = "invoice"
        REPORT = "report"
        STATUS = "status"
        TRACK = "track"

    def __init__(  # pylint: disable=too-many-arguments
        self,
        filename: str | Path | None = None,
        directory: str | Path | None = None,
        client: str | None = None,
        client_config_file: str | Path | None = None,
        me_config_file: str | Path | None = None,
        **kwargs,
    ):
        """Initialize class."""
        super().__init__(**kwargs)
        self.client_config = load_client_config(client_config_file)
        self.client = client or DEFAULT_CLIENT
        if self.client not in self.client_config.clients:
            msg = f"Client {self.client} not in client config."
            self.logger.warning(msg)
            print(msg)
        self.me = load_me_config(me_config_file)
        dir_path = Path(directory) if directory else DEFAULT_OUTPUT_DIR
        if not filename:
            # if not self.client:
            #     filename = DEFAULT_FILENAME
            # elif (
            #     self.client in self.client_config
            #     and "filename" in self.client_config[self.client]
            # ):
            #     filename = self.client_config[self.client]["filename"]
            # else:
            #     filename = f"{self.client}.csv"
            if self.client in self.client_config.clients:
                filename = Path(
                    self.client_config.clients[self.client].filename
                )
            else:
                filename = f"{self.client}.csv"
        assert filename
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
        totals, _ = self.generate_report(filter_task, start_date, end_date)

        if not totals:
            print("No matching entries found.")
            return

        print("Time spent per task (in hours):")
        for task, seconds in totals.items():
            print(f"  {task}: {seconds / 3600:.2f} h")
        total_time = sum(totals.values())
        print(f"\nTotal time: {total_time / 3600:.2f} h")

    def generate_report(
        self,
        filter_task: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ):
        """Generate a report, which can be printed or turned into an invoice."""
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
        # first_date = (
        #     datetime.combine(start_date, datetime.time()) if start_date else datetime.now()
        # )
        # last_date = datetime.combine(end_date, datetime.time()) if end_date else datetime.now()
        first_date = start_dt or datetime.today().date()
        last_date = end_dt or datetime.today().date()

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
                # print(f"first_date ({type(first_date)}): {first_date}")
                # print(f"start_time ({type(start_time)}): {start_time}")
                first_date = min(first_date, start_time)
                last_date = max(last_date, end_time)
                totals[task] += duration
                # print(f"Current totals: {totals}")
        return totals, (first_date, last_date)

    def generate_invoice(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        filter_task: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        invoice_filename: str | Path | None = None,
        invoice_template: str | Path | None = None,
        invoice_state_file: str | Path | None = None,
    ):
        """Generate an invoice based on tracked time."""
        # 1. Change "report" method to give the report values for this
        #    in "run_report", and then just use those values to print.
        totals, dates = self.generate_report(filter_task, start_date, end_date)
        first_date, last_date = dates
        # 2. Create a "clients.json" file containing things like name,
        #    address, phone number, email, rate, csv_filename, etc.
        #    Have the tracker's filepath object extract from there too?
        # 3. Create a LaTeX jinja2 template for the invoice.
        # 4. Create a default outputs/invoices dir, and a default invoice
        #    filename (YYYY_MM_DD-client_invoice.pdf).
        if not invoice_filename:
            DEFAULT_INVOICE_DIR.mkdir(parents=True, exist_ok=True)
            invoice_filename = DEFAULT_INVOICE_DIR / (
                f"{datetime.today().strftime('%Y_%m_%d')}-"
                f"{self.client}_invoice.pdf"
            )
        else:
            invoice_filename = Path(invoice_filename)
        invoice_template = (
            Path(invoice_template)
            if invoice_template
            else (
                DEFAULT_INVOICE_TEMPLATE
                if DEFAULT_INVOICE_TEMPLATE.exists()
                else SAMPLE_INVOICE_TEMPLATE
            )
        )
        # Build the items list:
        items = []
        total = 0.0
        rate = self.client_config.clients[self.client].rate
        for task, seconds in totals.items():
            hours = seconds / 3600
            subtotal = hours * rate
            items.append(
                {
                    "task": task,
                    "hours": hours,
                    "rate": rate,
                    "total": subtotal,
                }
            )
            total += subtotal
        invoice_template_path = invoice_template.parent
        invoice_template_filename = invoice_template.name
        # Load 'me' and invoice state info:
        if self.me.logo_path:
            self.me.logo_path = prepare_logo_for_latex(
                self.me.logo_path, invoice_filename.parent
            )
        invoice_number = get_next_invoice_number(invoice_state_file)
        # Load and render LaTeX template:
        env = Environment(
            loader=FileSystemLoader(invoice_template_path),
            block_start_string="((*",
            block_end_string="*))",
            variable_start_string="(((",
            variable_end_string=")))",
            comment_start_string="((#",
            comment_end_string="#))",
        )
        env.filters["latex_breaks"] = lambda s: s.replace("\n", r"\\")
        template = env.get_template(invoice_template_filename)
        rendered_tex = template.render(
            client=self.client_config.clients[self.client],
            date=datetime.now().strftime("%m/%d/%Y"),
            items=items,
            total=total,
            start_date=first_date.strftime("%m/%d/%Y"),
            end_date=last_date.strftime("%m/%d/%Y"),
            me=self.me,
            invoice_number=invoice_number,
        )
        # Write and compile:
        tex_path = invoice_filename.with_suffix(".tex")
        with open(tex_path, "w", encoding="utf8") as f:
            f.write(rendered_tex)
        try:  # pylint: disable=too-many-try-statements
            _ = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-shell-escape",
                    tex_path.name,
                ],
                cwd=tex_path.parent,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.logger.info(f"✅ Invoice created: {invoice_filename}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.warning("❌ Failed to compile LaTeX invoice: %s", e)
            if hasattr(e, "stdout") and e.stdout:
                self.logger.warning("📄 STDOUT:\n%s", e.stdout)
            if hasattr(e, "stderr") and e.stderr:
                self.logger.warning("🐞 STDERR:\n%s", e.stderr)

    @staticmethod
    def init_config():
        """Initialize the tracker environment with
        a client config file and an invoice template."""
        client_config_src = SAMPLE_CLIENT_CONFIG_FILE
        client_config_dst = DEFAULT_CLIENT_CONFIG_FILE

        template_src = SAMPLE_INVOICE_TEMPLATE
        template_dst = DEFAULT_INVOICE_TEMPLATE

        me_config_src = SAMPLE_ME_CONFIG_FILE
        me_config_dst = DEFAULT_ME_CONFIG_FILE

        invoice_state_config_src = SAMPLE_INVOICE_STATE_CONFIG_FILE
        invoice_state_config_dst = DEFAULT_INVOICE_STATE_CONFIG_FILE

        srcs = (
            client_config_src,
            template_src,
            me_config_src,
            invoice_state_config_src,
        )
        dsts = (
            client_config_dst,
            template_dst,
            me_config_dst,
            invoice_state_config_dst,
        )

        for src, dst in zip(srcs, dsts):
            if not dst.exists():
                shutil.copy(src, dst)
