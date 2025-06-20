"""This file contains tests for the invoice_state_models.py file."""

import json
import warnings

from time_tracker.config import InvoiceState

COULD_NOT_SAVE_STATE = "Could not save InvoiceState"


def test_increment():
    """Test the increment method."""
    four = 4
    state = InvoiceState(last_invoice_number=3)
    new_number = state.increment()
    assert new_number == four
    assert state.last_invoice_number == four


def test_save_to_existing_path(tmp_path):
    """Test saving to a valid path."""
    five = 5
    path = tmp_path / "invoice_state.json"
    path.write_text("")  # Ensure file exists

    state = InvoiceState(last_invoice_number=five)
    state.save(path)

    saved_data = json.loads(path.read_text())
    assert saved_data["last_invoice_number"] == five


def test_save_to_missing_path_warns(tmp_path):
    """Test saving to a non-existent path issues a warning."""
    one = 1
    two = 2
    bad_path = tmp_path / "nonexistent_dir" / "invoice_state.json"
    state = InvoiceState(last_invoice_number=two)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        state.save(bad_path)

        assert len(w) == one
        assert issubclass(w[-1].category, Warning)
        assert COULD_NOT_SAVE_STATE in str(w[-1].message)


def test_load_from_existing_file(tmp_path):
    """Test loading from a valid invoice state file."""
    ten = 10
    data = {"last_invoice_number": ten}
    file = tmp_path / "invoice_state.json"
    file.write_text(json.dumps(data))

    loaded = InvoiceState.load(file)
    assert isinstance(loaded, InvoiceState)
    assert loaded.last_invoice_number == ten


def test_load_from_missing_file_returns_default(tmp_path):
    """Test that loading from a missing file returns default InvoiceState."""
    file = tmp_path / "missing.json"
    loaded = InvoiceState.load(file)
    assert isinstance(loaded, InvoiceState)
    assert loaded.last_invoice_number == 0


def test_load_from_none_returns_default():
    """Test that loading from None returns default."""
    loaded = InvoiceState.load(None)
    assert isinstance(loaded, InvoiceState)
    assert loaded.last_invoice_number == 0


def test_save_with_none_path_warns():
    """Test that save with None warns."""
    one = 1
    state = InvoiceState()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        state.save(None)
        assert len(w) == one
        assert COULD_NOT_SAVE_STATE in str(w[-1].message)
