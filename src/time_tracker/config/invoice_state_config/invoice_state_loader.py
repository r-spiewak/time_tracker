"""This file contains functions related to loading invoice states."""

from pathlib import Path

from time_tracker.constants import DEFAULT_INVOICE_STATE_CONFIG_FILE

from .invoice_state_models import InvoiceState


def get_next_invoice_number(counter_file: str | Path | None = None) -> int:
    """Get the next invoice counter number."""
    # if counter_file and Path(counter_file).exists():
    #     with counter_file.open("r") as f:
    #         data = json.load(f)
    # else:
    #     data = {"last_invoice_number": 0}

    # data["last_invoice_number"] += 1

    # with counter_file.open("w") as f:
    #     json.dump(data, f)
    if not counter_file or not Path(counter_file).exists():
        counter_file = DEFAULT_INVOICE_STATE_CONFIG_FILE

    state = InvoiceState.load(counter_file)
    invoice_number = state.increment()
    state.save(counter_file)

    return invoice_number
