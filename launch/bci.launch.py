"""General launcher for the ros2neuro BCI pipeline.

Combines, for now: EEG acquisition (LSL backend), XDF session recording, and
the two-class threshold game controller. More nodes (game_bridge, other
acquisition backends, etc.) will be added here later.

`framerate` has no default on purpose: it depends on the actual EEG headset
and stream configuration, and guessing a wrong value would silently produce
mis-timed data rather than fail loudly.

Usage:
    ros2 launch launchers_bci bci.launch.py framerate:=512
    ros2 launch launchers_bci bci.launch.py framerate:=512 subject:=sub-01 session:=01 threshold_1:=0.25
"""

from __future__ import annotations

from ament_index_python.packages import get_package_share_directory
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
    lsl_default_config = get_package_share_directory("ros2neuro_acquisition_lsl") + "/config/lsl_configuration.yaml"

    launch_args = [
        DeclareLaunchArgument(
            "acquisition_config",
            default_value=lsl_default_config,
            description="Acquisition parameter file (defaults to the LSL backend's config).",
        ),
        DeclareLaunchArgument(
            "framerate",
            description="EEG acquisition framerate in Hz -- required, see module docstring for why.",
        ),
        DeclareLaunchArgument("output_directory", default_value=".", description="Recorder output directory"),
        DeclareLaunchArgument("subject", default_value="unknown", description="Recorder subject id"),
        DeclareLaunchArgument("session", default_value="", description="Recorder session id"),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the threshold controller")
            for name, default in THRESHOLD_DEFAULTS.items()
        ),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the threshold controller")
            for name, default in CONTROLLER_EXTRA_DEFAULTS.items()
        ),
    ]

    acquisition_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros2neuro_acquisition"), "launch", "acquisition.launch.xml"])
        ),
        launch_arguments={
            "config": LaunchConfiguration("acquisition_config"),
            "framerate": LaunchConfiguration("framerate"),
        }.items(),
    )

    recorder_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros2neuro_recorder_xdf"), "launch", "xdf_recorder.launch.py"])
        ),
        launch_arguments={
            "output_directory": LaunchConfiguration("output_directory"),
            "subject": LaunchConfiguration("subject"),
            "session": LaunchConfiguration("session"),
        }.items(),
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

    return LaunchDescription(
        [*launch_args, acquisition_launch, recorder_launch, controller_launch, wheel_launch]
    )
