import typer
from typing import Optional
from typing_extensions import Annotated

app = typer.Typer()

@app.command()
def main(
    data: Annotated[str, typer.Option(...,"--data","-d")],
    percentage: Annotated[Optional[int], typer.Option("--percentage","-p")] = 10,
) -> int:
    """Main function."""

    # Do stuff here.
    print("It worked!")
    print(f"data: {data}")
    print(f"percentage: {percentage}")

    return 0

def run() -> None:
    app()

if __name__ == "__main__":
    app()
