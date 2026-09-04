"""Same control path as control_gdf.launch.py (GDF playback + a
game_controller threshold controller + the passive wheel + game_bridge + an
XDF recorder), but with the real decoder detached: asyncronous_test.launch.xml
runs acquisition(gdf) -> filters -> buffer -> blink_detector (gate) -> integrator
with NO decoder_node in between, and it's on you to supply classification
manually, in a separate interactive terminal:

    ros2 run ros2neuro_decoder_py keyboard_decoder_node \\
        --ros-args -p output_topic:=/classification/prediction_raw

Hold the left arrow to simulate maximal left-hand evidence (class_a=1,
class_b=0), hold the right arrow for maximal right-hand evidence (class_a=0,
class_b=1), release for a neutral/undecided prediction -- see that node's
docstring. It publishes onto /classification/prediction_raw, the topic
blink_detector (see asyncronous_test.launch.xml) gates into
/classification/prediction, the one the integrator actually subscribes to --
so a real blink on artifact_channels still freezes the wheel/game even while
testing with the keyboard decoder. It must be `ros2 run`, never
`ros2 launch` (same terminal/termios constraint as game_controller's
dummy_keyboard_controller).

Usage:
    ros2 launch launchers_bci control_test.launch.py
    ros2 launch launchers_bci control_test.launch.py target:=host th_extreme_right:=0.25
    ros2 launch launchers_bci control_test.launch.py controller:=no_dead_zone
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
# training_controller.cpp) for this to stay consistent everywhere. Matches
# keyboard_decoder_node's own left_class_id/right_class_id defaults
# (769/770).
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
    "th_extreme_right": "0.25",  # right edge
    "th_right": "0.35",  # center-right edge
    "th_left": "0.65",  # center-left edge
    "th_extreme_left": "0.75",  # left edge
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
    "subject": "test",
    "session": "",
}


def generate_launch_description() -> LaunchDescription:
    launch_args = [
        DeclareLaunchArgument("target", default_value="local", description="game_bridge target: local or host"),
        DeclareLaunchArgument(
            "controller",
            default_value="no_dead_zone",
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
            PathJoinSubstitution([FindPackageShare("launchers_bci"), "launch", "test", "asyncronous_test.launch.xml"])
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
                # (see asyncronous_test.launch.xml's filters remap).
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
