"""Package constants."""

from enum import Enum
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_PATH = CONFIG_DIR / "defaults.yaml"

DEFAULT_FILENAME = "tracked_time.csv"
DEFAULT_OUTPUT_DIR = Path("outputs")


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
