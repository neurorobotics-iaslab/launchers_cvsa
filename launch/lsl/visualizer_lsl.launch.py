"""Standalone LSL acquisition + ros2neuro_visualizer, no filters/decoder/integrator.

Starts just the LSL acquisition node (same plugin/config as
asyncronous.launch.xml) and points ros2neuro_visualizer at its output
(/acquisition/neurodata, /acquisition/neurodata_info) so the raw EEG signal
can be inspected live after connecting to an LSL stream, without running the
rest of the classification pipeline.

Usage:
    ros2 launch launchers_bci lsl/visualizer_lsl.launch.py
    ros2 launch launchers_bci lsl/visualizer_lsl.launch.py stream_name:=my_stream
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        DeclareLaunchArgument("stream_name", default_value="LiveAmpSN-054211-0242", description="LSL stream name to connect to (empty: any)"),
        DeclareLaunchArgument("stream_type", default_value="EEG", description="LSL stream type to connect to"),
        DeclareLaunchArgument("framerate", default_value="20.0", description="acquisition publish framerate (Hz)"),
    ]

    acquisition_node = Node(
        package="ros2neuro_acquisition",
        executable="acquisition",
        name="acquisition",
        output="screen",
        parameters=[
            {
                "acquisition.plugin": "ros2neuro::acquisition::LSLDevice",
                "acquisition.autostart": True,
                "acquisition.reopen": True,
                "acquisition.framerate": ParameterValue(LaunchConfiguration("framerate"), value_type=float),
                "acquisition.stream_type": ParameterValue(LaunchConfiguration("stream_type"), value_type=str),
                "acquisition.stream_name": ParameterValue(LaunchConfiguration("stream_name"), value_type=str),
                "acquisition.max_buffered_samples": 5120,
                "acquisition.sensors.eeg.enable": True,
                "acquisition.sensors.eeg.name": "EEG",
                "acquisition.sensors.exg.enable": False,
                "acquisition.sensors.exg.name": "EXG",
                "acquisition.triggers.trigger.enable": False,
                "acquisition.triggers.trigger.name": "TRI",
            }
        ],
    )

    visualizer_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros2neuro_visualizer"), "launch", "visualizer.launch.py"])
        ),
    )

    return LaunchDescription([*launch_args, acquisition_node, visualizer_launch])
