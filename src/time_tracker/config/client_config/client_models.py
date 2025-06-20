"""This file holds classes to hold client information."""

from typing import Any

from pydantic import BaseModel, field_validator

from ..base_config import Party


class Client(Party):
    """Configuration for Client parties to a contract."""

    rate: float
    filename: str

    @field_validator("rate")
    @classmethod
    def positive_rate(cls, v: Any):
        """Validate that the rate is positive."""
        if v <= 0:
            raise ValueError("Rate must be positive.")
        return v


class ClientConfig(BaseModel):
    """Configurations for Clients."""

    clients: dict[str, Client]
