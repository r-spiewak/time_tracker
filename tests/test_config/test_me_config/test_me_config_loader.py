"""This file has tests for me_config_loader.py."""

import json
from pathlib import Path

import pytest

from time_tracker.config import Me
from time_tracker.config.me_config.me_config_loader import (
    check_svg_support,
    load_me_config,
    prepare_logo_for_latex,
)

SVG_LOGO_REQUIRES = "SVG logo requires"
UNSUPPORTED_FILE_TYPE = "Unsupported logo file type"


def test_load_me_config_with_provided_file(tmp_path):
    """Test loading from a valid provided config file."""
    test_user = "Test User"
    me_file = tmp_path / "me.json"
    me_file.write_text(
        json.dumps(
            {
                "name": test_user,
                "address": "123 Test Ave\nCity",
                "email": "test@example.com",
                "phone": "301-555-1234",
            }
        )
    )

    me = load_me_config(me_file)
    assert isinstance(me, Me)
    assert me.name == test_user


def test_load_me_config_fallback_default_exists(tmp_path, mocker):
    """Test fallback to DEFAULT_ME_CONFIG_FILE when none provided."""
    default_user = "Default User"
    default_path = tmp_path / "default_me.json"
    default_path.write_text(
        json.dumps(
            {
                "name": default_user,
                "address": "456 Default Blvd\nCity",
                "email": "default@example.com",
                "phone": "201-555-5678",
            }
        )
    )

    mocker.patch(
        "time_tracker.config.me_config.me_config_loader.DEFAULT_ME_CONFIG_FILE",
        default_path,
    )
    mocker.patch(
        "time_tracker.config.me_config.me_config_loader.SAMPLE_ME_CONFIG_FILE",
        Path("doesnt-matter.json"),
    )

    me = load_me_config(None)
    assert me.name == default_user


def test_load_me_config_fallback_sample_used(tmp_path, mocker):
    """Test fallback to SAMPLE_ME_CONFIG_FILE when default does not exist."""
    sample_user = "Sample User"
    sample_path = tmp_path / "sample_me.json"
    sample_path.write_text(
        json.dumps(
            {
                "name": sample_user,
                "address": "789 Sample Rd\nCity",
                "email": "sample@example.com",
                "phone": "301-555-9999",
            }
        )
    )

    mocker.patch(
        "time_tracker.config.me_config.me_config_loader.DEFAULT_ME_CONFIG_FILE",
        tmp_path / "missing.json",
    )
    mocker.patch(
        "time_tracker.config.me_config.me_config_loader.SAMPLE_ME_CONFIG_FILE",
        sample_path,
    )

    me = load_me_config(None)
    assert me.name == sample_user


def test_check_svg_support_inkscape_found(mocker):
    """Test prepare_logo_for_latex with inkscape found."""
    inkscape = "inkscape"
    mocker.patch("shutil.which", side_effect=lambda x: x == inkscape)
    assert check_svg_support() == inkscape


def test_check_svg_support_rsvg_convert_found(mocker):
    """Test prepare_logo_for_latex with rsvg-convert found."""
    rsvg_convert = "rsvg-convert"
    mocker.patch("shutil.which", side_effect=lambda x: x == rsvg_convert)
    assert check_svg_support() == rsvg_convert


def test_check_svg_support_not_found(mocker):
    """Test prepare_logo_for_latex with svg external programs not found."""
    mocker.patch("shutil.which", return_value=None)
    with pytest.raises(RuntimeError) as excinfo:
        check_svg_support()
    assert SVG_LOGO_REQUIRES in str(excinfo.value)


def test_prepare_logo_for_latex_supported_type(tmp_path):
    """Test prepare_logo_for_latex with supported file extension."""
    latex_dir = tmp_path / "latex"
    latex_dir.mkdir()

    logo_path = tmp_path / "logo.png"
    logo_path.write_text("fake logo data")

    rel_path = prepare_logo_for_latex(logo_path, latex_dir)
    assert rel_path == str(
        logo_path.resolve().relative_to(latex_dir.resolve(), walk_up=True)
    )


def test_prepare_logo_for_latex_svg_checks_support(tmp_path, mocker):
    """Test prepare_logo_for_latex with svg checks."""
    latex_dir = tmp_path / "latex"
    latex_dir.mkdir()

    logo_path = tmp_path / "logo.svg"
    logo_path.write_text("fake svg data")

    mock_check = mocker.patch(
        "time_tracker.config.me_config.me_config_loader.check_svg_support"
    )
    rel_path = prepare_logo_for_latex(logo_path, latex_dir)
    mock_check.assert_called_once()
    assert rel_path.endswith("logo.svg")


def test_prepare_logo_for_latex_missing_file(tmp_path):
    """Test prepare_logo_for_latex with missing file."""
    missing_logo = tmp_path / "missing.pdf"
    result = prepare_logo_for_latex(missing_logo, tmp_path)
    assert result is None


def test_prepare_logo_for_latex_unsupported_extension(tmp_path):
    """Test prepare_logo_for_latex with unsupported file extension."""
    latex_dir = tmp_path / "latex"
    latex_dir.mkdir()

    bad_logo = tmp_path / "bad.txt"
    bad_logo.write_text("not allowed")

    with pytest.raises(ValueError) as excinfo:
        prepare_logo_for_latex(bad_logo, latex_dir)

    assert UNSUPPORTED_FILE_TYPE in str(excinfo.value)
