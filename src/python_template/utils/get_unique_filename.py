"""This file contains a function to get unique filenames."""

import re
from pathlib import Path

from python_template.logger.logger import LoggerMixin


def get_unique_filename(
    out_file: str | Path,
    logger_filename: str | Path | None = None,
    verbosity: int = 0,
) -> Path:
    """Get a unique filename.

    Args:
        out_file (str | Path): Initial filename.
        logger_filename (str | Path | None): Filename (and path)
            to which to write log. If None, writes to a file in
            the local logs directory (relative to the calling
            directory) with the filename given by the current
            timestamp and class name, with the estension ".log".
            Dafaults to None.
        verbosity (int): How much and what level of logging to include.
            Higher values indicates more logging. Defaults to 0
            (warnings).

    Returns:
        Path: The unique output filename.
    """
    # return_string = isinstance(out_file, str)
    out_file = Path(out_file)
    logger = LoggerMixin(
        logger_filename=logger_filename, verbosity=verbosity
    ).logger
    logger.debug_with_category(
        "Initial output image filename: %s",
        str(out_file),
        category=logger.debugLevels.TRACE,
    )

    while out_file.exists():  # pylint: disable=while-used
        logger.debug_with_category(
            "Output image name %s exists. Renaming.",
            str(out_file),
            category=logger.debugLevels.TRACE,
        )
        stem = out_file.stem  # Get filename without extension.
        suffix = out_file.suffix  # Get extension with dot.

        # Check if the filename already ends with a number in parentheses:
        # match = re.search(r"(.*?) \((\d+)\)$", stem)
        if match := re.search(r"(.*?) \((\d+)\)$", stem):
            base_name = match.group(1)
            number = int(match.group(2)) + 1
            new_stem = f"{base_name} ({number})"
        else:
            new_stem = f"{stem} (1)"

        out_file = out_file.with_name(new_stem + suffix)
        logger.debug_with_category(
            "New filename attempt: %s",
            str(out_file),
            category=logger.debugLevels.TRACE,
        )

    # return str(out_file) if return_string else out_file
    return out_file
