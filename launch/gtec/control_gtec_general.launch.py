"""Full MI pipeline (live g.USBamp acquisition, see asyncronous.launch.xml)
+ the asynchronous/continuous game control path: controller_bridge_gtec.launch.xml
picks and wires up a game_controller threshold controller -- either
controlWithDeathZone.launch.py (dead zone between commands, reset at the
0.0/1.0 extremes) or controlNoDeadZone.launch.py (no dead zone, reset at the
outer thresholds instead), via its `controller` argument -- plus game_bridge,
via its `target` argument (local or host). Also starts the passive wheel in
control mode, plus an XDF recorder for the session (the recorder node is
built directly here, same as calibration.launch.py/evaluation.launch.py --
no dependency on ros2neuro_recorder_xdf's own launch file). Point a local
game server at game_bridge first (see the top-level repo README's
dummy-mode instructions).

All controller/bridge defaults (thresholds, command mapping, periods,
with_reset, controller, target) live in controller_bridge_gtec.launch.xml,
not here -- edit that file (and rebuild launchers_bci) to retune them. See
control_gtec_pong.launch.py for the pong-specific command mapping/periods.

Usage:
    ros2 launch launchers_bci control_gtec_general.launch.py
    ros2 launch launchers_bci control_gtec_general.launch.py target:=host th_extreme_right:=0.25
    ros2 launch launchers_bci control_gtec_general.launch.py controller:=with_dead_zone
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

RECORDER_DEFAULTS = {
    "output_directory": "./recordings",
    "subject": "paolo",
    "session": "",
}

# Forwarded to asyncronous.launch.xml's blink_detector node -- see
# ros2neuro_artifact_blink/src/blink_detector_node.cpp for what each one does.
BLINK_DEFAULTS = {
    "artifact_channels": "[FP1, FP2]",
    "freeze_duration_sec": "1.0",
    "threshold_vertical": "60.0",
    "threshold_horizontal": "60.0",
}


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the recorder")
            for name, default in RECORDER_DEFAULTS.items()
        ),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for blink_detector")
            for name, default in BLINK_DEFAULTS.items()
        ),
    ]

    pipeline_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("launchers_bci"), "launch", "gtec", "asyncronous.launch.xml"])
        ),
        launch_arguments={name: LaunchConfiguration(name) for name in BLINK_DEFAULTS}.items(),
    )

    controller_bridge_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("launchers_bci"), "launch", "gtec", "controller_bridge_gtec.launch.xml"]
            )
        ),
    )

    wheel_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros2neuro_feedback_wheel"), "launch", "wheel.launch.xml"])
        ),
        launch_arguments={
            "thresholds": [
                "[",
                LaunchConfiguration("th_extreme_right"),
                ", ",
                LaunchConfiguration("th_right"),
                ", ",
                LaunchConfiguration("th_left"),
                ", ",
                LaunchConfiguration("th_extreme_left"),
                "]",
            ],
            "mode": "control",
            "input_topic": LaunchConfiguration("control_topic"),
        }.items(),
    )

    recorder_node = Node(
        package="ros2neuro_recorder",
        executable="recorder",
        name="recorder",
        output="screen",
        parameters=[
            {
                "plugin": "ros2neuro::recorder::XDFRecorder",
                # acquisition publishes on its private "~/neurodata" topic
                # (see asyncronous.launch.xml's filters remap).
                "topic_data": "/acquisition/neurodata",
                "topic_info": "/acquisition/neurodata_info",
                "topic_event": "/neuroevent",
                # NeuroRecorderNode reads "output"/"recorder.output", not
                # "output_directory".
                # value_type=str: without it, launch infers the parameter
                # type from the string's content, so a numeric-looking
                # session/subject/dir (e.g. session:="1") turns into an
                # integer parameter and crashes the node (it declares these
                # as std::string -> rclcpp::exceptions::InvalidParameterTypeException).
                "output": ParameterValue(LaunchConfiguration("output_directory"), value_type=str),
                "subject": ParameterValue(LaunchConfiguration("subject"), value_type=str),
                "session": ParameterValue(LaunchConfiguration("session"), value_type=str),
                "modality": "control",
                "xdf.file_type": "gdf",
            }
        ],
    )

    return LaunchDescription(
        [*launch_args, pipeline_launch, controller_bridge_launch, wheel_launch, recorder_node]
    )
