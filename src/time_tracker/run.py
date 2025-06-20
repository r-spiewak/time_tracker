"""Run the script_profits app."""

import typer
from typing_extensions import Annotated

from time_tracker.tracker import TimeTracker

app = typer.Typer()
state = {"verbosity": 0}


@app.command()
def main(  # pylint: disable=too-many-arguments
    action: Annotated[
        str,
        typer.Option("--action", "-a", help="What to do with the tracker."),
    ] = "track",
    task: Annotated[
        str,
        typer.Option("--task", "-t", help="Task name or description."),
    ] = "",
    filename: Annotated[
        str | None, typer.Option("--filename", "-f", help="CSV filename.")
    ] = None,
    directory: Annotated[
        str,
        typer.Option("--directory", "-d", help="Directory to store the file."),
    ] = "",
    start_date: Annotated[
        str,
        typer.Option(
            "--start-date", "-s", help="Start date filter (YYYY-MM-DD)."
        ),
    ] = "",
    end_date: Annotated[
        str,
        typer.Option("--end-date", "-e", help="End date filter (YYYY-MM-DD)."),
    ] = "",
    verbosity: Annotated[
        int, typer.Option("--verbosity", "-v", count=True)
    ] = 0,
) -> int:
    """Main function to call the script_profit methods."""

    # Do stuff here.
    tracker = TimeTracker(filename=filename, directory=directory)
    # print("It worked!")
    if verbosity > 0:
        print(f"Verbosity: {verbosity}")
        state["verbosity"] = verbosity
    if action == tracker.actions.TRACK.value:
        tracker.track(task=task)
    elif action == tracker.actions.STATUS.value:
        tracker.status()
    elif action == tracker.actions.REPORT.value:
        tracker.report(
            filter_task=task, start_date=start_date, end_date=end_date
        )
    else:
        tracker.track(task=task)
    # return call_function(state, data, percentage)
    # A comment?
    return 0


# @app.callback()
# def verbosity_level(
#     ctx: typer.Context,
#     #verbosity: Annotated[Optional[List[bool]], typer.Option(...,"--verbosity","-v")] = [False],
#     verbosity: Annotated[Optional[int], typer.Option("--verbosity","-v",count=True)]
# ) -> int:
#     """
#     Manage users in the awesome CLI app.
#     """
#     #level = sum(verbosity)
#     level = verbosity
#     if level > 0:
#         print(f"Verbosity: {level}")
#         state["verbosity"] = level
#     if ctx.invoked_subcommand is not None:
#         ctx.invoke(typer.main.get_command(app).get_command(ctx, "main"))
#     return 0


def run() -> None:
    """Entrypoint for poetry."""
    app()


if __name__ == "__main__":
    app()
