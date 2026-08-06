"""Full MI pipeline (GDF playback, see mi_pipeline.launch.xml) + a
calibration training session: game_controller's training_controller
(modality:=calibration, fake feedback via Autopilot) plus the passive wheel
in training mode.

Usage:
    ros2 launch launchers_bci calibration.launch.py
    ros2 launch launchers_bci calibration.launch.py classes:="[773, 771, 783]" trials:="[10, 10, 5]"
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        DeclareLaunchArgument("classes", default_value="[773, 771]", description="MI class ids for the session"),
        DeclareLaunchArgument("trials", default_value="[10, 10]", description="Trial count per class"),
    ]

    pipeline_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("launchers_bci"), "launch", "mi_pipeline.launch.xml"])
        ),
    )

    training_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("game_controller"), "launch", "training.launch.py"])
        ),
        launch_arguments={
            "modality": "calibration",
            "classes": LaunchConfiguration("classes"),
            "trials": LaunchConfiguration("trials"),
        }.items(),
    )

    return LaunchDescription([*launch_args, pipeline_launch, training_launch])
