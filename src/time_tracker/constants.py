"""Package constants."""

from enum import Enum
from pathlib import Path

REPO_HOME = Path(__file__).parent.parent.parent

CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_PATH = CONFIG_DIR / "defaults.yaml"

DEFAULT_FILENAME = "tracked_time.csv"
DEFAULT_OUTPUT_DIR = Path("outputs")

DEFAULT_CLIENT = "client1"
DEFAULT_CLIENT_CONFIG_DIR = REPO_HOME / "config"
DEFAULT_CLIENT_CONFIG_FILE = DEFAULT_CLIENT_CONFIG_DIR / "clients.json"
SAMPLE_CLIENT_CONFIG_FILE = DEFAULT_CLIENT_CONFIG_DIR / "sample_clients.json"
DEFAULT_ME_CONFIG_FILE = DEFAULT_CLIENT_CONFIG_DIR / "me.json"
SAMPLE_ME_CONFIG_FILE = DEFAULT_CLIENT_CONFIG_DIR / "sample_me.json"
DEFAULT_INVOICE_STATE_CONFIG_FILE = (
    DEFAULT_CLIENT_CONFIG_DIR / "invoice_state.json"
)
SAMPLE_INVOICE_STATE_CONFIG_FILE = (
    DEFAULT_CLIENT_CONFIG_DIR / "sample_invoice_state.json"
)

DEFAULT_INVOICE_DIR = DEFAULT_OUTPUT_DIR / "invoices"
DEFAULT_TEMPLATE_DIR = REPO_HOME / "templates"
DEFAULT_INVOICE_TEMPLATE = DEFAULT_TEMPLATE_DIR / "invoice.tex.jinja2"
SAMPLE_INVOICE_TEMPLATE = DEFAULT_TEMPLATE_DIR / "sample_invoice.tex.jinja2"


class ColumnHeaders(Enum):
    """Enum class containing the valid column headers."""

    START = "start"
    END = "end"
    DURATION = "duration (s)"
    TASK = "task"


HEADERS = [
    ColumnHeaders.START.value,
    ColumnHeaders.END.value,
    ColumnHeaders.DURATION.value,
    ColumnHeaders.TASK.value,
]
