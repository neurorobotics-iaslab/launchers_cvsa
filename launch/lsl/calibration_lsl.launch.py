"""Calibration session: includes calibration_pipeline.launch.xml (live LSL
acquisition -> filters -> buffer, no classifier -- part of this same
launchers_bci package) and directly launches game_controller's
training_controller (modality:=calibration, fake feedback via Autopilot),
the passive wheel in training mode, and an XDF recorder (so the session
produces a new GDF, e.g. for training a classifier later) -- no dependency
on game_controller's own training.launch.py file or on
ros2neuro_recorder_xdf's launch file (the recorder node is built directly
here, same as training_controller/wheel).

`thresholds` is passed as-is to both training_controller (which uses it to
decide hit/miss) and the wheel (whose markers are purely visual), so the
markers always sit exactly where a hit is actually triggered.

Usage:
    ros2 launch launchers_bci calibration_lsl.launch.py
    ros2 launch launchers_bci calibration_lsl.launch.py classes:="[773, 771, 783]" trials:="[10, 10, 5]"
    ros2 launch launchers_bci calibration_lsl.launch.py thresholds:="[0.75, 0.25]"
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

TRAINING_DEFAULTS = {
    "classes": "[769, 770]",
    "trials": "[10, 10]",
    "thresholds": "[0.8, 0.2]",
    "control_topic": "/game_controller/control",
    "event_topic": "/neuroevent",
}

RECORDER_DEFAULTS = {
    "output_directory": "./recordings",
    "subject": "vernon72",
    "session": "",
}


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        DeclareLaunchArgument(name, default_value=default, description=f"{name} for the training controller")
        for name, default in TRAINING_DEFAULTS.items()
    ] + [
        DeclareLaunchArgument(name, default_value=default, description=f"{name} for the recorder")
        for name, default in RECORDER_DEFAULTS.items()
    ]

    pipeline_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("launchers_bci"), "launch", "lsl", "calibration_pipeline.launch.xml"]
            )
        ),
    )

    training_node = Node(
        package="game_controller",
        executable="training_controller",
        name="training_controller",
        output="screen",
        parameters=[
            {
                "modality": "calibration",
                "classes": LaunchConfiguration("classes"),
                "trials": LaunchConfiguration("trials"),
                "thresholds": LaunchConfiguration("thresholds"),
                "control_topic": LaunchConfiguration("control_topic"),
                "event_topic": LaunchConfiguration("event_topic"),
            }
        ],
    )

    wheel_node = Node(
        package="ros2neuro_feedback_wheel",
        executable="wheel",
        name="wheel",
        output="screen",
        parameters=[
            {
                "mode": "training",
                "input_topic": LaunchConfiguration("control_topic"),
                "event_topic": LaunchConfiguration("event_topic"),
                "classes": LaunchConfiguration("classes"),
                # Same values (same order) passed to training_controller
                # above, so the markers sit exactly where a hit is triggered.
                "thresholds": LaunchConfiguration("thresholds"),
            }
        ],
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
                # (see calibration_pipeline.launch.xml's filters remap).
                "topic_data": "/acquisition/neurodata",
                "topic_info": "/acquisition/neurodata_info",
                "topic_event": LaunchConfiguration("event_topic"),
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
                "modality": "calibration",
                "xdf.file_type": "gdf",
            }
        ],
    )

    return LaunchDescription([*launch_args, pipeline_launch, training_node, wheel_node, recorder_node])
