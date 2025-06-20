"""This file contains models representing me, the user of the tracker module."""

from pathlib import Path

from pydantic import field_validator

from ..base_config import Party


class Me(Party):
    """Config class for the 'me' (the user of the tracker) party to a contract."""

    company_name: str | None = None  # Optional field
    logo_path: str | Path | None = None  # Optional field

    # @validator("", pre=True, always=True)
    @field_validator("logo_path")
    @classmethod
    def validate_logo_path(cls, v):
        """Validate that the logo_path is valid and is of valid extension."""
        if not v:
            return None
        try:  # pylint: disable=too-many-try-statements
            path = Path(v)
            if not path.exists():
                return None  # silently ignore missing logo
            allowed = {".pdf", ".png", ".jpeg", ".jpg", ".eps", ".svg"}
            if path.suffix.lower() not in allowed:
                return None
            return str(path)
        except Exception:  # pylint: disable=broad-exception-caught
            return None
