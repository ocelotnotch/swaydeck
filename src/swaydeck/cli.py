"""Command-line interface for SwayDeck."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from .layout import (
    LayoutError,
    save_current_layout,
)
from .ui import run_tui


APP_NAME = "SwayDeck"
APP_VERSION = "0.3.1"


def usage() -> str:
    return "\n".join(
        [
            "Usage: swaydeck [OPTION]",
            "",
            "TUI display manager for Sway.",
            "",
            "Options:",
            "  -h, --help        Show this help and exit",
            "  -V, --version     Show version and exit",
            "      --save-layout Save current layout and reload Sway",
        ]
    )


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = list(
        sys.argv[1:]
        if argv is None
        else argv
    )

    if not args:
        return run_tui()

    if len(args) > 1:
        print(
            "swaydeck: too many arguments",
            file=sys.stderr,
        )

        print(
            usage(),
            file=sys.stderr,
        )

        return 2

    option = args[0]

    if option in {
        "-h",
        "--help",
    }:
        print(
            usage()
        )

        return 0

    if option in {
        "-V",
        "--version",
    }:
        print(
            f"{APP_NAME} {APP_VERSION}"
        )

        return 0

    if option == "--save-layout":
        try:
            path = save_current_layout()

        except (
            LayoutError,
            ValueError,
        ) as exc:
            print(
                f"ERROR: {exc}",
                file=sys.stderr,
            )

            return 1

        print(
            f"✓ Current layout saved: {path}"
        )

        return 0

    print(
        f"swaydeck: unknown option: {option}",
        file=sys.stderr,
    )

    print(
        usage(),
        file=sys.stderr,
    )

    return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
