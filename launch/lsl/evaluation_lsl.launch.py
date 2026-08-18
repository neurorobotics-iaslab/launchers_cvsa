"""Full MI pipeline (live LSL stream, see evaluation_pipeline.launch.xml) +
an evaluation training session: game_controller's training_controller
(modality:=evaluation, real classifier output from the pipeline) plus the
passive wheel in training mode, plus an XDF recorder for the session (the
recorder node is built directly here, same as calibration.launch.py -- no
dependency on ros2neuro_recorder_xdf's own launch file).

Usage:
    ros2 launch launchers_bci evaluation_lsl.launch.py
    ros2 launch launchers_bci evaluation_lsl.launch.py classes:="[773, 771, 783]" trials:="[10, 10, 5]"
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
    "output_directory": ".",
    "subject": "paolo",
    "session": "",
}


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        DeclareLaunchArgument("classes", default_value="[773, 771]", description="MI class ids for the session"),
        DeclareLaunchArgument("trials", default_value="[10, 10]", description="Trial count per class"),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the recorder")
            for name, default in RECORDER_DEFAULTS.items()
        ),
    ]

    pipeline_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("launchers_bci"), "launch", "lsl", "evaluation_pipeline.launch.xml"]
            )
        ),
    )

    training_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("game_controller"), "launch", "training.launch.py"])
        ),
        launch_arguments={
            "modality": "evaluation",
            "classes": LaunchConfiguration("classes"),
            "trials": LaunchConfiguration("trials"),
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
                # (see evaluation_pipeline.launch.xml's filters remap).
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
                "modality": "evaluation",
                "xdf.file_type": "gdf",
            }
        ],
    )

    return LaunchDescription([*launch_args, pipeline_launch, training_launch, recorder_node])
