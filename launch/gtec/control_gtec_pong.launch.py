"""Same pipeline as control_gtec_general.launch.py, but with the pong-specific
no_dead_zone command mapping/periods baked in as defaults instead of
control_gtec_general.launch.py's own (see controller_bridge_gtec.launch.xml):
right_command/center_command/left_command rotate one step (B/C/A ->
D/A/C -- pong's wheel-up input is 'A', not 'C'), and right/left_command_period_sec
drop from 0.5s to 0.15s for snappier one-shot turns. Everything else
(thresholds, controller, target, with_reset, ...) is unchanged and still
overridable the same way.

Usage:
    ros2 launch launchers_bci control_gtec_pong.launch.py
    ros2 launch launchers_bci control_gtec_pong.launch.py target:=host th_extreme_right:=0.25
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

PONG_OVERRIDES = {
    "right_command": "INPUT_D",
    "center_command": "INPUT_A",
    "left_command": "INPUT_C",
    "right_command_period_sec": "0.15",
    "left_command_period_sec": "0.15",
    "th_right": "0.45",
    "th_left": "0.55",
    "th_extreme_right": "0.3",
    "th_extreme_left": "0.7",
    "with_reset": "true",
}


def generate_launch_description() -> LaunchDescription:
    # Only the pong-specific overrides are passed through; every other arg
    # (target, th_right, controller, ...) keeps control_gtec_general.launch.py's
    # own default and is still overridable the same way on the CLI.
    general_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("launchers_bci"), "launch", "gtec", "control_gtec_general.launch.py"]
            )
        ),
        launch_arguments=PONG_OVERRIDES.items(),
    )

    return LaunchDescription([general_launch])
