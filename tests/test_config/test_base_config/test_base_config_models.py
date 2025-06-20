"""This file has tests for base_config_models.py."""

import pytest

from time_tracker.config import Party


def test_party_invalid_address():
    """Test Party with an invalid address."""
    with pytest.raises(ValueError):
        Party(
            name="bob",
            address="123 Fourth Ave, Five City, Sixth State, 00000",
            email="bob@example.com",
            phone="987-654-3210",
        )


def test_party_invalid_phone():
    """Test Party with an invalid phone."""
    with pytest.raises(ValueError):
        Party(
            name="bob",
            address="123 Fourth Ave\nFive City, Sixth State 00000",
            email="bob@example.com",
            phone="987-654-3210-1234",
        )
