import typer

app = typer.Typer()

@app.command()
def main() -> int:
    """Main function."""

    # Do stuff here.
    print("It worked!")

    return 0


if __name__ == "__main__":
    main()
