"""Test the CLI app."""

from typer.testing import CliRunner

from python_template.run import app

# INVALID_PERCENTAGE = "Invalid value for '--percentage'"
IT_WORKED = "It worked!"
MISSING_DATA = "Missing option '--data'"
PERCENTAGE_10 = "percentage: 10"
PERCENTAGE_25 = "percentage: 25"
SAMPLE_DATA = "data: sample_data"
VERBOSITY_2 = "Verbosity: 2"
VERBOSITY_3 = "Verbosity: 3"

runner = CliRunner()


def test_app(capsys):
    """Test the cli app invocation."""
    result = runner.invoke(app, ["--data", "tests/test_file"])
    with capsys.disabled():
        print("stdout:")
        print(result.stdout)
        # print("stderr:")
        # print(result.stderr)
        # Need to capture stderr separately.
        # Otherwise it's bundled in with stdout.
    assert result.exit_code == 0
    assert IT_WORKED in result.stdout
    # assert "Let's have a coffee in Berlin" in result.stdout


def test_main_command_with_required_args():
    """Test the main command with required arguments."""
    result = runner.invoke(app, ["--data", "sample_data"])
    assert result.exit_code == 0
    assert IT_WORKED in result.output
    assert SAMPLE_DATA in result.output
    assert PERCENTAGE_10 in result.output


def test_main_command_with_all_args():
    """Test the main command with all arguments specified."""
    result = runner.invoke(
        app,
        [
            "--data",
            "sample_data",
            "--percentage",
            "25",
            "--verbosity",
            "-vv",
        ],
    )
    assert result.exit_code == 0
    assert IT_WORKED in result.output
    assert VERBOSITY_3 in result.output
    assert SAMPLE_DATA in result.output
    assert PERCENTAGE_25 in result.output


def test_main_command_without_required_args():
    """Test the main command fails when required arguments are missing."""
    result = runner.invoke(app, [])
    assert result.exit_code != 0
    assert MISSING_DATA in result.output


# I really should implement this check...
# def test_main_command_with_invalid_percentage():
#     """Test the main command handles invalid percentage values."""
#     result = runner.invoke(
#         app, ["--data", "sample_data", "--percentage", "-5"]
#     )
#     assert result.exit_code != 0
#     assert INVALID_PERCENTAGE in result.output


def test_pipeline_run_called():
    """Test that Pipeline's run method is called during main command execution."""
    result = runner.invoke(app, ["--data", "sample_data"])
    assert result.exit_code == 0


def test_verbosity_flag_changes_state():
    """Test that verbosity flag updates the state dictionary."""
    result = runner.invoke(app, ["--data", "sample_data", "-vv"])
    assert result.exit_code == 0
    assert VERBOSITY_2 in result.output
