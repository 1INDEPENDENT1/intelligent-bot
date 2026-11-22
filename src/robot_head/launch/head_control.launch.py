"""Compose existing description launch with the native head actuator."""
from pathlib import Path
from tempfile import TemporaryDirectory
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from robot_head.simulation_model import generate_model
from robot_head.model import load_limits


def _setup(context):
    share = Path(get_package_share_directory("robot_head"))
    description = Path(get_package_share_directory("robot_description"))
    config = yaml.safe_load((share / "config/head_control.yaml").read_text())
    temporary = TemporaryDirectory(prefix="robot-head-")
    override = LaunchConfiguration("model_file").perform(context)
    model = Path(override) if override else Path(temporary.name) / "head.urdf"
    try:
        if override:
            load_limits(model)
        else:
            generate_model(description / "urdf/robot.urdf", model, config["gains"])
    except Exception:
        temporary.cleanup()
        raise
    def cleanup(context):
        temporary.cleanup()
        return []
    return [
        RegisterEventHandler(OnShutdown(on_shutdown=[OpaqueFunction(function=cleanup)])),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(description / "launch/gazebo.launch.py")),
            launch_arguments={"model_file": str(model), "gui": LaunchConfiguration("gui")}.items()),
        Node(package="robot_head", executable="head_pitch_node", output="screen",
             parameters=[{"model_file": str(model), "use_sim_time": True,
                          "reference_speed_scale": config["reference_speed_scale"]}]),
        Node(package="ros_gz_bridge", executable="parameter_bridge", output="screen",
             parameters=[{"config_file": str(share / "config/bridge.yaml"), "use_sim_time": True}]),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("model_file", default_value="",
            description="Optional preconfigured URDF; empty generates the native head actuator"),
        DeclareLaunchArgument("gui", default_value="true", choices=["true", "false"]),
        OpaqueFunction(function=_setup),
    ])
