"""This file has tests for me_config_models.py."""

from pathlib import Path

from time_tracker.config import Me


def test_me_with_all_fields(tmp_path):
    """Test full Me instance with valid logo_path."""
    alice = "Alice"
    awesome = "Awesome Inc."

    logo = tmp_path / "logo.pdf"
    logo.write_text("PDF content")

    me = Me(
        name=alice,
        address="123 Main St\nCity",
        phone="301-555-1234",
        email="alice@example.com",
        company_name=awesome,
        logo_path=str(logo),
    )

    assert me.name == alice
    assert me.company_name == awesome
    assert me.logo_path == str(logo)


def test_me_logo_path_none():
    """Test that None logo_path is accepted and remains None."""
    me = Me(
        name="Bob",
        address="456 Side St\nCity",
        phone="301-555-5678",
        email="bob@example.com",
        logo_path=None,
    )
    assert me.logo_path is None


def test_me_logo_path_nonexistent():
    """Test that nonexistent path is silently ignored (set to None)."""
    me = Me(
        name="Carol",
        address="789 Road\nCity",
        phone="501-666-0000",
        email="carol@example.com",
        logo_path="nonexistent.svg",
    )
    assert me.logo_path is None


def test_me_logo_path_invalid_extension(tmp_path):
    """Test that an existing file with disallowed extension is ignored."""
    bad_logo = tmp_path / "logo.txt"
    bad_logo.write_text("Invalid logo")
    me = Me(
        name="Dave",
        address="1010 Elm\nCity",
        phone="501-333-4321",
        email="dave@example.com",
        logo_path=str(bad_logo),
    )
    assert me.logo_path is None


def test_me_logo_path_with_exception(monkeypatch, tmp_path):
    """Test fallback to None if Path() call or property raises an error."""

    # class BrokenPath:
    #     def __fspath__(self):
    #         raise RuntimeError("Path error")

    real_path = tmp_path / "logo.pdf"
    real_path.write_text("PDF content")

    def raise_on_exists(self):
        raise RuntimeError("Simulated path failure")

    monkeypatch.setattr(Path, "exists", raise_on_exists)

    me = Me(
        name="Eve",
        address="1212 Ivy\nCity",
        phone="301-555-8765",
        email="eve@example.com",
        # logo_path=BrokenPath(),
        logo_path=str(real_path),  # Still passes type validation
    )
    assert me.logo_path is None
