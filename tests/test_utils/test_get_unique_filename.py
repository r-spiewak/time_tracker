"""This file contains tests for the function get_unique_file."""

from pathlib import Path

from time_tracker.utils import get_unique_filename

DATA_1_CSV = "data (1).csv"
FILE_NUM_1_TEXT = "file2023 (1).txt"
LOG_3_LOG = "log (3).log"
RESULT_1_TEXT = "result (1).txt"
RESULT_5_TEXT = "result (5).txt"
THING_1_TEXT = "thing (1).txt"


def test_new_file_does_not_exist(temp_dir):
    """Tests when file doesn't exist."""
    out_path = temp_dir / "result.txt"
    logger_filename = temp_dir / "log.log"
    assert not out_path.exists()
    result = get_unique_filename(out_path, logger_filename=logger_filename)
    assert result == out_path


def test_single_existing_file(temp_dir):
    """Tests when file already exists."""
    out_path = temp_dir / "result.txt"
    out_path.write_text("dummy content")
    logger_filename = temp_dir / "log.log"
    unique = get_unique_filename(out_path, logger_filename=logger_filename)
    assert unique != out_path
    assert unique.name == RESULT_1_TEXT


def test_multiple_existing_files(temp_dir):
    """Tests when multiple versions of the filename already exist."""
    # Create result.txt, result (1).txt, ..., result (4).txt
    for i in range(5):
        suffix = f" ({i})" if i > 0 else ""
        (temp_dir / f"result{suffix}.txt").write_text("dummy")

    logger_filename = temp_dir / "log.log"
    next_unique = get_unique_filename(
        temp_dir / "result.txt", logger_filename=logger_filename
    )
    assert next_unique.name == RESULT_5_TEXT


def test_filename_with_different_suffix(temp_dir):
    """Tests when file exists with a different extension."""
    (temp_dir / "data.csv").write_text("a,b,c")
    logger_filename = temp_dir / "log.log"
    unique = get_unique_filename(
        temp_dir / "data.csv", logger_filename=logger_filename
    )
    assert unique.name == DATA_1_CSV


def test_filename_with_number_but_not_suffix(temp_dir):
    """Tests when filename contains a number, but not in the vesion format."""
    # If filename is like 'file2023.txt', that shouldn't be mistaken as suffix
    file = temp_dir / "file2023.txt"
    file.write_text("dummy")
    logger_filename = temp_dir / "log.log"
    result = get_unique_filename(file, logger_filename=logger_filename)
    assert result.name == FILE_NUM_1_TEXT


def test_filename_with_existing_paren_suffix(temp_dir):
    """Tests when multiple versions of the file exist."""
    (temp_dir / "log (1).log").write_text("dummy")
    (temp_dir / "log (2).log").write_text("dummy")
    (temp_dir / "log.log").write_text("dummy")
    logger_filename = temp_dir / "log.log"
    result = get_unique_filename(
        temp_dir / "log.log", logger_filename=logger_filename
    )
    assert result.name == LOG_3_LOG


def test_preserve_directory_path(temp_dir):
    """Tests that the directory path is preserved."""
    # Check that it returns a path in the same directory
    (temp_dir / "output.txt").write_text("dummy")
    logger_filename = temp_dir / "log.log"
    unique = get_unique_filename(
        temp_dir / "output.txt", logger_filename=logger_filename
    )
    assert unique.parent == temp_dir


def test_work_with_path_object(temp_dir):
    """Tests that it works with Path objects."""
    # Ensure it accepts a Path object
    path_obj = temp_dir / "thing.txt"
    path_obj.write_text("hi")
    logger_filename = temp_dir / "log.log"
    result = get_unique_filename(path_obj, logger_filename=logger_filename)
    assert isinstance(result, Path)
    assert result.name == THING_1_TEXT
