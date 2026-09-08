"""fzf terminal UI for SwayDeck."""

from __future__ import annotations

import shutil
import subprocess

from .layout import save_current_layout
from .mirror import (
    mirror_alive,
    stop_mirror,
)
from .settings import (
    apply_orientation,
    apply_scale,
    transform_label,
)
from .sway import get_outputs
from .topology import (
    projection_mode,
    select_primary,
)
from .workflows import (
    apply_duplicate,
    apply_enable_all,
    apply_extend_right,
    apply_pc_only,
    apply_second_only,
    arrange_displays,
)


FZF_THEME = (
    "--height=90%",
    "--layout=reverse",
    "--border=rounded",
    "--cycle",
    "--no-multi",
    "--no-sort",
    "--exact",
    "--nth=1",
    "--info=inline-right",
    "--prompt=> ",
    "--pointer=▶",
    (
        "--color="
        "fg:#565a6e,"
        "fg+:#34548a:bold,"
        "hl:#5a4a78,"
        "hl+:#34548a:bold,"
        "info:#9699a3,"
        "prompt:#34548a:bold,"
        "pointer:#34548a:bold,"
        "header:#343b58,"
        "border:#9699a3,"
        "bg:-1,"
        "bg+:-1,"
        "gutter:-1"
    ),
)


class UIError(RuntimeError):
    """Raised when the SwayDeck UI cannot run."""


def choose(
    prompt: str,
    header: str,
    options: list[str],
) -> str | None:
    fzf = shutil.which(
        "fzf"
    )

    if fzf is None:
        raise UIError(
            "fzf is not installed or not available in PATH"
        )

    result = subprocess.run(
        [
            fzf,
            *FZF_THEME,
            f"--prompt={prompt}",
            f"--header={header}",
        ],
        input=(
            "\n".join(options)
            + "\n"
        ),
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return None

    selected = result.stdout.strip()

    return (
        selected
        if selected
        else None
    )


def choice_key(
    selection: str,
) -> str:
    return selection.split(
        None,
        1,
    )[0]


def choice_value(
    selection: str,
) -> str:
    parts = selection.split(
        None,
        1,
    )

    if len(parts) != 2:
        return ""

    return parts[1].strip()


def numbered(
    values: list[str],
) -> list[str]:
    return [
        f"{index}  {value}"
        for index, value in enumerate(
            values,
            start=1,
        )
    ]


def pick(
    prompt: str,
    values: list[str],
) -> str | None:
    if not values:
        return None

    if len(values) == 1:
        return values[0]

    selection = choose(
        prompt,
        "Type number + Enter",
        numbered(
            values
        ),
    )

    if selection is None:
        return None

    return choice_value(
        selection
    )


def notify(
    message: str,
) -> None:
    binary = shutil.which(
        "notify-send"
    )

    if binary is None:
        return

    subprocess.run(
        [
            binary,
            "-a",
            "SwayDeck",
            "Display",
            message,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def summary(
    outputs,
    primary: str,
) -> str:
    lines: list[str] = []

    for output in outputs:
        role = (
            "PRIMARY"
            if output.name == primary
            else "EXTERNAL"
        )

        state = (
            "ACTIVE"
            if output.active
            else "OFF"
        )

        if (
            output.active
            and output.rect is not None
        ):
            geometry = (
                f"{output.rect.width}"
                f"x{output.rect.height}"
                f" @ {output.rect.x},"
                f"{output.rect.y}"
            )
        else:
            geometry = "-"

        scale = (
            str(output.scale)
            if output.scale is not None
            else "-"
        )

        lines.append(
            f"{role:<8}  "
            f"{output.name:<12}  "
            f"{state:<6}  "
            f"{geometry:<23} "
            f"scale {scale} | "
            f"transform {output.transform}"
        )

    return "\n".join(
        lines
    )


def extend_menu() -> str:
    selection = choose(
        "Extend > ",
        "Type shortcut + Enter",
        [
            "a  Extend + arrange position",
            "r  Extend + reset all to the right",
        ],
    )

    if selection is None:
        return "Ready"

    key = choice_key(
        selection
    )

    if key == "r":
        stop_mirror()

        apply_extend_right()

        notify(
            "Extend — displays arranged to the right"
        )

        return (
            "✓ Extend: displays arranged to the right"
        )

    if key != "a":
        return "Ready"

    stop_mirror()

    apply_enable_all()

    outputs = get_outputs()

    active = [
        output
        for output in outputs
        if output.active
    ]

    primary = select_primary(
        outputs
    )

    if (
        primary is None
        or len(active) < 2
    ):
        return "Enable Extend first"

    movable = [
        output.name
        for output in active
        if output.name != primary
    ]

    target = pick(
        "Move > ",
        movable,
    )

    if target is None:
        return "Ready"

    if len(active) == 2:
        anchor = primary

    else:
        anchors = [
            output.name
            for output in active
            if output.name != target
        ]

        anchor = pick(
            "Relative > ",
            anchors,
        )

    if anchor is None:
        return "Ready"

    direction_selection = choose(
        "Position > ",
        (
            f"{target} relative "
            f"to {anchor}"
        ),
        [
            "1  Right",
            "2  Left",
            "3  Above",
            "4  Below",
        ],
    )

    if direction_selection is None:
        return "Ready"

    direction = choice_value(
        direction_selection
    )

    arrange_displays(
        target,
        anchor,
        direction,
    )

    notify(
        f"{target} → {direction} of {anchor}"
    )

    return (
        f"✓ {target} → "
        f"{direction} of {anchor}"
    )


def second_only_menu() -> str:
    outputs = get_outputs()

    primary = select_primary(
        outputs
    )

    if primary is None:
        return "No Sway outputs detected"

    externals = [
        output.name
        for output in outputs
        if output.name != primary
    ]

    target = pick(
        "External > ",
        externals,
    )

    if target is None:
        return "No external display detected"

    stop_mirror()

    apply_second_only(
        target
    )

    notify(
        f"Second screen only — {target}"
    )

    return (
        f"✓ Second screen only: {target}"
    )


def settings_menu() -> str:
    if mirror_alive():
        return (
            "Switch out of Duplicate before "
            "changing display settings"
        )

    outputs = get_outputs()

    active_names = [
        output.name
        for output in outputs
        if output.active
    ]

    target = pick(
        "Display > ",
        active_names,
    )

    if target is None:
        return "No active display detected"

    current = next(
        output
        for output in outputs
        if output.name == target
    )

    current_scale = (
        current.scale
        if current.scale is not None
        else "-"
    )

    selection = choose(
        "Settings > ",
        (
            f"{target} | "
            f"Scale: {current_scale}x | "
            f"Orientation: "
            f"{transform_label(current.transform)}"
        ),
        [
            "1  Scale",
            "2  Orientation",
            "b  Back",
        ],
    )

    if selection is None:
        return "Ready"

    key = choice_key(
        selection
    )

    if key == "b":
        return "Ready"

    if key == "1":
        selected = choose(
            "Scale > ",
            (
                f"{target} | "
                f"Current: {current_scale}x"
            ),
            [
                "1  1.00",
                "2  1.25",
                "3  1.50",
                "4  1.75",
                "5  2.00",
                "6  2.25",
                "7  2.50",
                "8  3.00",
            ],
        )

        if selected is None:
            return "Ready"

        scale = float(
            choice_value(
                selected
            )
        )

        apply_scale(
            target,
            scale,
        )

        notify(
            f"{target} scale → {scale}x"
        )

        return (
            f"✓ {target} scale → {scale}x"
        )

    if key == "2":
        selected = choose(
            "Orientation > ",
            (
                f"{target} | Current: "
                f"{transform_label(current.transform)}"
            ),
            [
                "1  Landscape",
                "2  Portrait",
                "3  Landscape flipped",
                "4  Portrait flipped",
            ],
        )

        if selected is None:
            return "Ready"

        transforms = {
            "1": "normal",
            "2": "90",
            "3": "180",
            "4": "270",
        }

        transform = transforms.get(
            choice_key(
                selected
            )
        )

        if transform is None:
            return "Ready"

        apply_orientation(
            target,
            transform,
        )

        label = transform_label(
            transform
        )

        notify(
            f"{target} orientation → {label}"
        )

        return (
            f"✓ {target} orientation → {label}"
        )

    return "Ready"


def run_tui() -> int:
    print(
        "\033]0;SwayDeck\007",
        end="",
        flush=True,
    )

    status = "Ready"

    while True:
        try:
            outputs = get_outputs()

            primary = select_primary(
                outputs
            )

            if primary is None:
                raise UIError(
                    "No Sway outputs detected"
                )

            if mirror_alive():
                mode = "Duplicate"
            else:
                mode = projection_mode(
                    outputs,
                    primary,
                )

            header = (
                "SwayDeck\n\n"
                f"Mode: {mode}  |  "
                f"Primary: {primary}\n\n"
                f"{summary(outputs, primary)}"
                "\n\n"
                f"Status: {status}"
            )

            selection = choose(
                "Display > ",
                header,
                [
                    "1  PC screen only",
                    "2  Duplicate",
                    "3  Extend",
                    "4  Second screen only",
                    "5  Display settings",
                    "6  Save current layout",
                    "q  Exit",
                ],
            )

            if selection is None:
                return 0

            key = choice_key(
                selection
            )

            if key == "q":
                return 0

            if key == "1":
                stop_mirror()

                apply_pc_only()

                status = (
                    "✓ PC screen only applied"
                )

                notify(
                    "PC screen only"
                )

            elif key == "2":
                apply_duplicate()

                status = (
                    "✓ Duplicate applied"
                )

                notify(
                    "Duplicate"
                )

            elif key == "3":
                status = extend_menu()

            elif key == "4":
                status = second_only_menu()

            elif key == "5":
                status = settings_menu()

            elif key == "6":
                path = save_current_layout()

                status = (
                    "✓ Current layout saved: "
                    f"{path}"
                )

                notify(
                    "Current display layout saved"
                )

        except (
            RuntimeError,
            ValueError,
        ) as exc:
            status = (
                f"ERROR: {exc}"
            )
