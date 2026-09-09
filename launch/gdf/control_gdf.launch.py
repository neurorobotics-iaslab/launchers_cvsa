"""Full MI pipeline (GDF playback, see asyncronous.launch.xml) + the
asynchronous/continuous game control path: a game_controller threshold
controller -- either controlWithDeathZone.launch.py (default, dead zone
between commands, reset at the 0.0/1.0 extremes) or controlNoDeadZone.launch.py
(no dead zone, reset at the outer thresholds instead), picked via the
`controller` argument -- plus the passive wheel in control mode, plus an XDF
recorder for the session (the recorder node is built directly here, same as
calibration.launch.py/evaluation.launch.py -- no dependency on
ros2neuro_recorder_xdf's own launch file). Also starts game_bridge -- point
a local game server at it first (see the top-level repo README's dummy-mode
instructions).

Usage:
    ros2 launch launchers_bci control_gdf.launch.py
    ros2 launch launchers_bci control_gdf.launch.py target:=host th_extreme_right:=0.25
    ros2 launch launchers_bci control_gdf.launch.py controller:=no_dead_zone
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

# Same four thresholds feed either controller variant (see the `controller`
# arg above); what each one bounds depends on which is selected. probability
# is values[0]/(values[0]+values[1]) (see TwoClassThresholdController's
# _derive_position): class_a (values[0]) is the numerator on purpose so it
# dominates towards probability 1 -> wheel LEFT -- class_a must be the FIRST
# class in the `classes` launch arg used by calibration/evaluation
# (classes[0] == Direction::Left == the blue threshold in calibration, see
# training_controller.cpp) for this to stay consistent everywhere.
#  - with_dead_zone (controlWithDeathZone.launch.py, default):
#      probability < th_extreme_right             -> INPUT_B, wheel all the way RIGHT (class_b)
#      th_extreme_right <= probability < th_right  -> dead zone (right-of-center)
#      th_right <= probability < th_left           -> INPUT_C, wheel CENTER (up)
#      th_left <= probability < th_extreme_left     -> dead zone (left-of-center)
#      probability >= th_extreme_left              -> INPUT_A, wheel all the way LEFT (class_a)
#  - no_dead_zone (controlNoDeadZone.launch.py): no dead zone, a command is
#    always sent; th_extreme_right/th_extreme_left instead mark when
#    (with_reset:=true) the integrator reset fires:
#      probability < th_right                      -> INPUT_B, wheel all the way RIGHT (class_b)
#      th_right <= probability < th_left            -> INPUT_C, wheel CENTER (up)
#      probability >= th_left                       -> INPUT_A, wheel all the way LEFT (class_a)
#      probability <= th_extreme_right or >= th_extreme_left -> integrator reset
THRESHOLD_DEFAULTS = {
    "th_extreme_right": "0.1",  # right edge
    "th_right": "0.25",  # center-right edge
    "th_left": "0.7",  # center-left edge
    "th_extreme_left": "0.85",  # left edge
}

CONTROLLER_EXTRA_DEFAULTS = {
    # command_period_sec only applies to with_dead_zone
    # (TwoClassThresholdController); left/right/center_command_period_sec
    # only apply to no_dead_zone (NoDeadZoneThresholdController's 3-state
    # machine -- CENTER defaults far shorter since it doubles as "keep going
    # forward"). Both sets are always forwarded; whichever controller isn't
    # selected simply doesn't declare the other set's parameters, so they're
    # ignored.
    "command_period_sec": "0.5",
    "right_command_period_sec": "0.5",
    "center_command_period_sec": "0.1",
    "left_command_period_sec": "0.5",
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
        DeclareLaunchArgument(
            "controller",
            default_value="with_dead_zone",
            description=(
                "game_controller variant: with_dead_zone (controlWithDeathZone.launch.py) "
                "or no_dead_zone (controlNoDeadZone.launch.py)"
            ),
        ),
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
            PathJoinSubstitution([FindPackageShare("launchers_bci"), "launch", "gdf", "asyncronous.launch.xml"])
        ),
    )

    controller_launch_file = PythonExpression(
        [
            "'controlWithDeathZone.launch.py' if '",
            LaunchConfiguration("controller"),
            "' == 'with_dead_zone' else 'controlNoDeadZone.launch.py'",
        ]
    )

    controller_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("game_controller"), "launch", controller_launch_file])
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
