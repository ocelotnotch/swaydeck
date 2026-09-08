"""SwayDeck Python API."""

from .executor import (
    execute_operation,
    execute_operations,
)
from .layout import (
    LayoutError,
    default_backup_dir,
    default_layout_file,
    generate_layout_config,
    layout_signature,
    save_current_layout,
)
from .mirror import (
    MirrorError,
    default_pid_file,
    mirror_alive,
    require_wl_mirror,
    start_mirror,
    stop_mirror,
)
from .models import (
    Output,
    Rect,
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
from .settings import (
    SettingsError,
    apply_orientation,
    apply_scale,
    transform_label,
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
from .topology import (
    projection_mode,
    select_primary,
    two_layout_direction,
)
from .workflows import (
    WorkflowError,
    apply_duplicate,
    apply_enable_all,
    apply_extend_right,
    apply_pc_only,
    apply_second_only,
    arrange_displays,
)


__all__ = [
    "DisableOp",
    "EnableOp",
    "LayoutError",
    "MirrorError",
    "Output",
    "OutputOperation",
    "PositionOp",
    "Rect",
    "SettingsError",
    "SwayCommandError",
    "SwayError",
    "SwayProtocolError",
    "WorkflowError",
    "apply_duplicate",
    "apply_enable_all",
    "apply_extend_right",
    "apply_orientation",
    "apply_pc_only",
    "apply_scale",
    "apply_second_only",
    "arrange_displays",
    "default_backup_dir",
    "default_layout_file",
    "default_pid_file",
    "disable_output",
    "enable_output",
    "execute_operation",
    "execute_operations",
    "generate_layout_config",
    "get_outputs",
    "layout_signature",
    "mirror_alive",
    "plan_arrange_multi",
    "plan_arrange_two",
    "plan_pc_only",
    "plan_right_chain",
    "plan_second_only",
    "position_output",
    "projection_mode",
    "require_wl_mirror",
    "run_sway_command",
    "save_current_layout",
    "scale_output",
    "select_primary",
    "start_mirror",
    "stop_mirror",
    "transform_label",
    "transform_output",
    "two_layout_direction",
]
