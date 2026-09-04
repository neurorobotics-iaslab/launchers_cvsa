"""Standalone g.USBamp acquisition + ros2neuro_visualizer, no filters/decoder/integrator.

Starts just the g.USBamp acquisition node (same plugin/config as
asyncronous.launch.xml) and points ros2neuro_visualizer at its output
(/acquisition/neurodata, /acquisition/neurodata_info) so the raw EEG signal
can be inspected live from the amplifier, without running the rest of the
classification pipeline.

Usage:
    ros2 launch launchers_bci gtec/visualizer_gtec.launch.py
    ros2 launch launchers_bci gtec/visualizer_gtec.launch.py device:=UB-2010.10.01
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
        DeclareLaunchArgument("device", default_value="", description="g.USBamp device serial (empty: first found)"),
        DeclareLaunchArgument("channels", default_value="16", description="number of acquired channels"),
        DeclareLaunchArgument("samplerate", default_value="512", description="acquisition sample rate (Hz)"),
        DeclareLaunchArgument("framerate", default_value="16.0", description="acquisition publish framerate (Hz)"),
    ]

    acquisition_node = Node(
        package="ros2neuro_acquisition",
        executable="acquisition",
        name="acquisition",
        output="screen",
        parameters=[
            {
                "acquisition.plugin": "ros2neuro::acquisition::GUSBampDevice",
                "acquisition.autostart": True,
                "acquisition.reopen": True,
                "acquisition.samplerate": ParameterValue(LaunchConfiguration("samplerate"), value_type=int),
                "acquisition.framerate": ParameterValue(LaunchConfiguration("framerate"), value_type=float),
                "acquisition.device": ParameterValue(LaunchConfiguration("device"), value_type=str),
                "acquisition.channels": ParameterValue(LaunchConfiguration("channels"), value_type=int),
                "acquisition.enable_trigger_line": True,
                "acquisition.scan_dio": True,
                "acquisition.slave_mode": False,
                "acquisition.enable_sc": False,
                "acquisition.bandpass_filter": -1,
                "acquisition.notch_filter": -1,
                "acquisition.bipolar_derivation": -2,
                "acquisition.sensors.eeg.enable": True,
                "acquisition.sensors.eeg.name": "EEG",
                "acquisition.sensors.eeg.labels": ["Fz", "FC3", "FC1", "FCz", "FC2", "FC4", "C3", "C1", "Cz", "C2", "C4", "FP1", "CP1", "CPz", "CP2", "FP2"],
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
