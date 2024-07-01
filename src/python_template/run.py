"""Run the script_profits app."""

import typer
from typing_extensions import Annotated

app = typer.Typer()
state = {"verbosity": 0}


@app.command()
def main(
    data: Annotated[str, typer.Option(..., "--data", "-d")],
    percentage: Annotated[int, typer.Option("--percentage", "-p")] = 10,
    verbosity: Annotated[
        int, typer.Option("--verbosity", "-v", count=True)
    ] = 0,
) -> int:
    """Main function to call the script_profit methods."""

    # Do stuff here.
    print("It worked!")
    if verbosity > 0:
        print(f"Verbosity: {verbosity}")
        state["verbosity"] = verbosity
    print(f"data: {data}")
    print(f"percentage: {percentage}")
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
