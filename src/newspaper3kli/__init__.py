"""Newspaper3k's command-line interface."""


def main() -> int:
    """Preserve the original ``newspaper3kli.main`` entrypoint."""
    from .cli import main as cli_main

    return cli_main()
