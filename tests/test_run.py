"""Test the CLI app."""

from typer.testing import CliRunner

from script_profits.run import app

runner = CliRunner()


def test_app(capsys):
    """Test the cli app invocation."""
    result = runner.invoke(app, ["--data", "tests/test_db.csv"])
    with capsys.disabled():
        print("stdout:")
        print(result.stdout)
        # print("stderr:")
        # print(result.stderr)
        # Need to capture stderr separately.
        # Otherwise it's bundled in with stdout.
    it_worked = "It worked!"
    assert result.exit_code == 0
    assert it_worked in result.stdout
    # assert "Let's have a coffee in Berlin" in result.stdout
