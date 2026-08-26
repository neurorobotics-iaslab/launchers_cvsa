"""Full MI pipeline (live g.USBamp acquisition, see asyncronous.launch.xml)
+ the asynchronous/continuous game control path:
two_class_threshold_controller (decides INPUT_A/C/B and sends to
game_bridge) plus the passive wheel in control mode, plus an XDF recorder
for the session (the recorder node is built directly here, same as
calibration.launch.py/evaluation.launch.py -- no dependency on
ros2neuro_recorder_xdf's own launch file). Also starts game_bridge -- point
a local game server at it first (see the top-level repo README's dummy-mode
instructions).

Usage:
    ros2 launch launchers_bci control_gtec.launch.py
    ros2 launch launchers_bci control_gtec.launch.py target:=host threshold_1:=0.25
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

THRESHOLD_DEFAULTS = {
    "threshold_1": "0.1",
    "threshold_2": "0.25",
    "threshold_3": "0.7",
    "threshold_4": "0.85",
}

CONTROLLER_EXTRA_DEFAULTS = {
    "command_period_sec": "0.5",
    "with_reset": "true",
    # IntegratorNode creates its reset service as "reset" (a relative name,
    # not "~/reset"), so it resolves to "/reset" -- NOT "/integrator/reset"
    # (that would only apply to a private "~/reset" name). See
    # ros2neuro_integrator/src/IntegratorNode.cpp.
    "reset_service_name": "/reset",
    "control_topic": "/game_controller/control",
}

RECORDER_DEFAULTS = {
    "output_directory": "./recordings",
    "subject": "paolo",
    "session": "",
}


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        DeclareLaunchArgument("target", default_value="local", description="game_bridge target: local or host"),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the threshold controller")
            for name, default in {**THRESHOLD_DEFAULTS, **CONTROLLER_EXTRA_DEFAULTS}.items()
        ),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the recorder")
            for name, default in RECORDER_DEFAULTS.items()
        ),
    ]

    pipeline_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("launchers_bci"), "launch", "gtec", "asyncronous.launch.xml"])
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
            "thresholds": [
                "[",
                LaunchConfiguration("threshold_1"),
                ", ",
                LaunchConfiguration("threshold_2"),
                ", ",
                LaunchConfiguration("threshold_3"),
                ", ",
                LaunchConfiguration("threshold_4"),
                "]",
            ],
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
        [*launch_args, pipeline_launch, controller_launch, wheel_launch, bridge_launch, recorder_node]
    )
