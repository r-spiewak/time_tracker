"""This file contains tests for the invoice_state_loader.py file."""

import json

from time_tracker.config import get_next_invoice_number


def test_get_next_invoice_number_with_valid_file(tmp_path):
    """Test incrementing the invoice number from a valid existing file."""
    four = 4
    file = tmp_path / "invoice_state.json"
    initial_data = {"last_invoice_number": 3}
    file.write_text(json.dumps(initial_data))

    result = get_next_invoice_number(counter_file=file)

    assert result == four
    new_data = json.loads(file.read_text())
    assert new_data["last_invoice_number"] == four


def test_get_next_invoice_number_with_missing_file_uses_default(
    mocker, tmp_path
):
    """Test fallback to DEFAULT_INVOICE_STATE_CONFIG_FILE if path is None or missing."""
    one = 1
    dummy_default = tmp_path / "default_invoice_state.json"
    dummy_default.write_text(json.dumps({"last_invoice_number": 0}))

    # Patch the constant to point to our test file
    mocker.patch(
        "time_tracker.config.invoice_state_config."
        "invoice_state_loader.DEFAULT_INVOICE_STATE_CONFIG_FILE",
        dummy_default,
    )

    result = get_next_invoice_number(counter_file=None)
    assert result == one

    new_data = json.loads(dummy_default.read_text())
    assert new_data["last_invoice_number"] == one


def test_get_next_invoice_number_with_nonexistent_path_uses_default(
    mocker, tmp_path
):
    """Test behavior when a nonexistent path is passed in."""
    two = 2
    nonexistent_path = tmp_path / "nonexistent.json"
    dummy_default = tmp_path / "fallback_invoice_state.json"
    dummy_default.write_text(json.dumps({"last_invoice_number": 1}))

    mocker.patch(
        "time_tracker.config.invoice_state_config."
        "invoice_state_loader.DEFAULT_INVOICE_STATE_CONFIG_FILE",
        dummy_default,
    )

    result = get_next_invoice_number(counter_file=nonexistent_path)
    assert result == two

    assert json.loads(dummy_default.read_text())["last_invoice_number"] == two
