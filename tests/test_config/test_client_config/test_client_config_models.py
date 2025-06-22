"""This file has tests for client_config_models.py."""

import pytest

from time_tracker.config import Client


def test_client_invalid_rate():
    """Test Client with an invalid rate."""
    with pytest.raises(ValueError):
        Client(
            name="bob",
            address="123 Fourth Ave\nFive City, Sixth State, 00000",
            email="bob@example.com",
            phone="901-654-3210",
            rate=-10,
            filename="file.csv",
        )
