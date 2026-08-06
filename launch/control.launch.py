"""Full MI pipeline (GDF playback, see mi_pipeline.launch.xml) + the
asynchronous/continuous game control path: two_class_threshold_controller
(decides INPUT_A/C/B and sends to game_bridge) plus the passive wheel in
control mode. Also starts game_bridge -- point a local game server at it
first (see the top-level repo README's dummy-mode instructions).

Usage:
    ros2 launch launchers_bci control.launch.py
    ros2 launch launchers_bci control.launch.py target:=host threshold_1:=0.25
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

THRESHOLD_DEFAULTS = {
    "threshold_1": "0.3",
    "threshold_2": "0.4",
    "threshold_3": "0.6",
    "threshold_4": "0.7",
}

CONTROLLER_EXTRA_DEFAULTS = {
    "command_period_sec": "0.5",
    "with_reset": "false",
    "reset_service_name": "/integrator/reset",
    "control_topic": "/game_controller/control",
}


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        DeclareLaunchArgument("target", default_value="local", description="game_bridge target: local or host"),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the threshold controller")
            for name, default in {**THRESHOLD_DEFAULTS, **CONTROLLER_EXTRA_DEFAULTS}.items()
        ),
    ]

    pipeline_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("launchers_bci"), "launch", "mi_pipeline.launch.xml"])
        ),
    )

    controller_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("game_controller"), "launch", "two_class_threshold.launch.py"])
        ),
        launch_arguments={
            name: LaunchConfiguration(name) for name in {**THRESHOLD_DEFAULTS, **CONTROLLER_EXTRA_DEFAULTS}
        }.items(),
    )

    wheel_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros2neuro_feedback_wheel"), "launch", "wheel.launch.xml"])
        ),
        launch_arguments={
            **{name: LaunchConfiguration(name) for name in THRESHOLD_DEFAULTS},
            "mode": "control",
            "input_topic": LaunchConfiguration("control_topic"),
        }.items(),
    )

    bridge_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("game_bridge"), "launch", "bridge.launch.py"])
        ),
        launch_arguments={"target": LaunchConfiguration("target")}.items(),
    )

    return LaunchDescription(
        [*launch_args, pipeline_launch, controller_launch, wheel_launch, bridge_launch]
    )
