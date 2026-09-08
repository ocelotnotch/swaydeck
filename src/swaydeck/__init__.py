"""Core Python components for SwayDeck."""

from .models import Output, Rect
from .mirror import (
    MirrorError,
    default_pid_file,
    mirror_alive,
    require_wl_mirror,
    start_mirror,
    stop_mirror,
)
from .executor import (
    execute_operation,
    execute_operations,
)
from .plans import (
    DisableOp,
    EnableOp,
    OutputOperation,
    PositionOp,
    plan_arrange_multi,
    plan_arrange_two,
    plan_pc_only,
    plan_right_chain,
    plan_second_only,
)
from .sway import (
    SwayCommandError,
    SwayError,
    SwayProtocolError,
    disable_output,
    enable_output,
    get_outputs,
    position_output,
    run_sway_command,
    scale_output,
    transform_output,
)
from .workflows import (
    WorkflowError,
    apply_duplicate,
    apply_extend_right,
    apply_pc_only,
    apply_second_only,
    arrange_displays,
)
from .topology import (
    projection_mode,
    select_primary,
    two_layout_direction,
)

__all__ = [
    "DisableOp",
    "EnableOp",
    "MirrorError",
    "Output",
    "OutputOperation",
    "PositionOp",
    "Rect",
    "SwayCommandError",
    "SwayError",
    "SwayProtocolError",
    "WorkflowError",
    "apply_duplicate",
    "apply_extend_right",
    "apply_pc_only",
    "apply_second_only",
    "arrange_displays",
    "default_pid_file",
    "mirror_alive",
    "require_wl_mirror",
    "start_mirror",
    "stop_mirror",
    "disable_output",
    "execute_operation",
    "execute_operations",
    "enable_output",
    "get_outputs",
    "plan_arrange_multi",
    "plan_arrange_two",
    "plan_pc_only",
    "plan_right_chain",
    "plan_second_only",
    "position_output",
    "projection_mode",
    "run_sway_command",
    "scale_output",
    "select_primary",
    "transform_output",
    "two_layout_direction",
]
