"""Full MI pipeline (live g.USBamp acquisition, see
evaluation_pipeline.launch.xml) + an evaluation training session:
game_controller's training_controller (modality:=evaluation, real classifier
output from the pipeline) plus the passive wheel in training mode, plus an
XDF recorder for the session. The training_controller/wheel pair and the
recorder node are all built directly here, same as calibration.launch.py --
no dependency on game_controller's training.launch.py or
ros2neuro_recorder_xdf's own launch file.

Usage:
    ros2 launch launchers_bci evaluation_gtec.launch.py
    ros2 launch launchers_bci evaluation_gtec.launch.py classes:="[773, 771, 783]" trials:="[10, 10, 5]"
    ros2 launch launchers_bci evaluation_gtec.launch.py threshold_vertical:=50.0 threshold_horizontal:=25.0
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
    "subject": "pafo27",
    "session": "",
}

# Forwarded to evaluation_pipeline.launch.xml's blink_detector node -- see
# ros2neuro_artifact_blink/src/blink_detector_node.cpp for what each one does.
BLINK_DEFAULTS = {
    "artifact_channels": "[FP1, FP2]",
    "freeze_duration_sec": "1.0",
    "threshold_vertical": "60.0",
    "threshold_horizontal": "60.0",
}

# Same defaults game_controller's training.launch.py declares for
# training_controller/wheel, minus modality (fixed to "evaluation" below) and
# classes/trials (already declared above).
TRAINING_DEFAULTS = {
    "thresholds": "[0.8, 0.2]",
    "control_topic": "/game_controller/control",
    "event_topic": "/neuroevent",
    "probability_topic": "/integrated/raw",
}


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        DeclareLaunchArgument("classes", default_value="[769, 770]", description="MI class ids for the session"),
        DeclareLaunchArgument("trials", default_value="[10, 10]", description="Trial count per class"),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the recorder")
            for name, default in RECORDER_DEFAULTS.items()
        ),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for blink_detector")
            for name, default in BLINK_DEFAULTS.items()
        ),
        *(
            DeclareLaunchArgument(name, default_value=default, description=f"{name} for the training controller")
            for name, default in TRAINING_DEFAULTS.items()
        ),
    ]

    pipeline_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("launchers_bci"), "launch", "gtec", "evaluation_pipeline.launch.xml"]
            )
        ),
        launch_arguments={name: LaunchConfiguration(name) for name in BLINK_DEFAULTS}.items(),
    )

    training_node = Node(
        package="game_controller",
        executable="training_controller",
        name="training_controller",
        output="screen",
        parameters=[
            {
                "modality": "evaluation",
                "classes": LaunchConfiguration("classes"),
                "trials": LaunchConfiguration("trials"),
                **{name: LaunchConfiguration(name) for name in TRAINING_DEFAULTS},
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
                # Same values training_controller uses to decide hit/miss, so
                # the wheel's markers sit exactly where a hit is triggered.
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

    return LaunchDescription([*launch_args, pipeline_launch, training_node, wheel_node, recorder_node])
