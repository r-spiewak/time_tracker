"""This file contains a function to load a 'me' config."""

import json
import shutil
from pathlib import Path

from time_tracker.constants import (
    DEFAULT_ME_CONFIG_FILE,
    SAMPLE_ME_CONFIG_FILE,
)

from ...config.load_config import settings
from .me_config_models import Me

ALLOWED_EXTS = {".pdf", ".png", ".jpeg", ".jpg", ".eps", ".svg"}

DEBUG_PRINTS = settings.debug_prints


def load_me_config(me_config_file: str | Path | None = None) -> Me:
    """Load a 'me' config file."""
    if (
        not me_config_file
        or not (me_config_file := Path(me_config_file)).exists()
    ):
        me_config_file = (
            DEFAULT_ME_CONFIG_FILE
            if DEFAULT_ME_CONFIG_FILE.exists()
            else SAMPLE_ME_CONFIG_FILE
        )
    with Path(me_config_file).open("r", encoding="utf8") as file:
        me_config = json.load(file)

    return Me(**me_config)


def check_svg_support():
    """Ensure a tool for .svg conversion (used by LaTeX) is available."""
    if shutil.which("inkscape"):
        return "inkscape"
    if shutil.which("rsvg-convert"):
        return "rsvg-convert"
    raise RuntimeError(
        "SVG logo requires either 'inkscape' or 'rsvg-convert' to be installed and in PATH. "
        f"Please install one of these tools or use a supported image format ({ALLOWED_EXTS})."
    )


def prepare_logo_for_latex(
    user_logo_path: str | Path, latex_dir: Path
) -> str | None:
    """Prepare a user_logo_path for input into a .tex file."""
    src = Path(user_logo_path).resolve()
    if not src.exists():
        return None
    if (ext := src.suffix.lower()) not in ALLOWED_EXTS:
        raise ValueError(
            f"Unsupported logo file type: {ext}. Allowed: {ALLOWED_EXTS}"
        )

    # SVG must be copied with the extension preserved:
    svg_ext = ".svg"
    if ext == svg_ext:
        # Check for LaTeX tool availability if desired (e.g. `inkscape`)
        check_svg_support()

    # shutil.copyfile(src, latex_dir / src.name)
    # return src.name  # Return full filename (with .svg)
    if DEBUG_PRINTS:
        print(
            f" Logo: {str(src.relative_to(latex_dir.absolute().resolve(), walk_up=True))}"
        )
    return str(src.relative_to(latex_dir.resolve(), walk_up=True))
