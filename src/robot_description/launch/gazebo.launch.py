"""Spawn the existing URDF in a self-contained Gazebo Harmonic world."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory("robot_description"))
    urdf = share / "urdf" / "robot.urdf"
    gazebo = Path(get_package_share_directory("ros_gz_sim"))
    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true",
                              choices=["true", "false"],
                              description="Start the Gazebo GUI"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(gazebo / "launch/gz_sim.launch.py")),
            launch_arguments={
                "gz_args": [PythonExpression([
                    "'-r ' if '", LaunchConfiguration("gui"),
                    "' == 'true' else '-r -s '"]),
                    str(share / "worlds/minimal.sdf")],
                "on_exit_shutdown": "true",
            }.items(),
        ),
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[{"robot_description": urdf.read_text(),
                          "use_sim_time": True}], output="screen"),
        Node(package="ros_gz_bridge", executable="parameter_bridge",
             parameters=[{"config_file": str(share / "config/bridge.yaml"),
                          "use_sim_time": True}], output="screen"),
        Node(package="ros_gz_sim", executable="create",
             arguments=["-world", "minimal", "-name", "my_robot",
                        "-file", str(urdf), "-z", "0.02"],
             output="screen"),
    ])