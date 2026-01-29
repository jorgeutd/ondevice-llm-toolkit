"""Module entrypoint for python -m odlt."""

from odlt.cli import app


def main() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    main()
