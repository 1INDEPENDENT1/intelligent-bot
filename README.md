# Robot workspace

A compact tracked companion robot project using ROS 2 Jazzy and Gazebo Harmonic
(Sim 8) on Ubuntu 24.04 in WSL2/WSLg. The current application is a geometry
prototype: a body, fixed track envelopes, and a passive head pitch joint in a
minimal simulated environment. Drive control, head actuation, sensing,
localization, and physical hardware integration are not implemented yet.

## Current packages

```text
robot_ws/
├── README.md
└── src/
    └── robot_description/
        └── README.md
```

| Package | Responsibility | Context documentation |
| --- | --- | --- |
| `robot_description` | Robot geometry, meshes, link/joint definitions, and the current Gazebo world, launch, and ROS bridge configuration. | [Package README](src/robot_description/README.md) |

`robot_description` is the only ROS 2 package directly under `src/`, so there
are no relationships or dependencies between local packages yet. It integrates
with the external `robot_state_publisher`, `ros_gz_sim`, and `ros_gz_bridge`
packages to spawn the model and expose simulation time, joint states, and TF.
Its README contains the recursive file map, runtime interfaces, dependencies,
geometry details, validation procedures, and limitations.

## Build and run

Run these commands inside WSL **Ubuntu-24.04**:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/robot_ws
colcon build --base-paths src --packages-select robot_description --symlink-install
source install/setup.bash
ros2 launch robot_description gazebo.launch.py
```

If dependencies are missing, install them from the workspace root before building:

```bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
```

For headless simulation, replace the launch command with:

```bash
ros2 launch robot_description gazebo.launch.py gui:=false
```

Source both ROS and the workspace environment in each new terminal. Run one
simulation instance at a time and stop it with Ctrl+C. See the
[package validation commands](src/robot_description/README.md#validation-commands)
for model conversion, ROS topic, and TF checks.
