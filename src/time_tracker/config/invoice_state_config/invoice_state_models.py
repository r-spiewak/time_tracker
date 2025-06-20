"""This file contains a model for invoice state operations."""

import json
import warnings
from pathlib import Path

from pydantic import BaseModel


class InvoiceState(BaseModel):
    """A class to hold invoice state attributes."""

    last_invoice_number: int = 0

    def increment(self) -> int:
        """Increment by one the last_invoice_number attribute."""
        self.last_invoice_number += 1
        return self.last_invoice_number

    def save(self, path: str | Path | None):
        """Save an InvoiceState config as a .json file."""
        if path and Path(path).exists():
            with Path(path).open("w", encoding="utf-8") as f:
                json.dump(self.model_dump(), f, indent=4)
        else:
            warnings.warn(
                Warning(
                    f"Could not save InvoiceState, path {path} does not exist.",
                )
            )

    @classmethod
    def load(cls, path: str | Path | None = None) -> "InvoiceState":
        """Load an invoice_state.json file into an InvoiceState config class."""
        if path and Path(path).exists():
            with Path(path).open("r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        return cls()
