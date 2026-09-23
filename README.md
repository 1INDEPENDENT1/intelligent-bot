# Compact tracked companion robot

We are building a small tracked robot companion inspired by Anki Vector, with
a distinctive spherical head and a low, compact body. The head is the robot's
main visual feature: it should give the robot the presence of a character while
keeping the mechanical design simple.

## Product concept

- **A large spherical head partially recessed into the body.** Approximately
  half of the sphere sits inside the body, with the rest exposed. Its pitch axis
  passes through the sphere's geometric centre, within the upper body.
- **A low, unified silhouette.** The body supports the head from both sides and
  conceals the mounting mechanism. Recessing the head keeps the robot compact
  and leaves room for the pivot and servo inside the body.
- **Two independently driven tracks as the intended locomotion system.** One
  track sits on each side of the body.
- **An extended rear compartment** for electronics, power, and drive components.
- **No arms, lifting mechanism, or external manipulators.** The character and
  proportions centre on the head and tracked body.

The first engineering model focuses on the head position and depth, body length,
track placement, and overall proportions. Decorative exterior details belong to
a later stage; simplified collision shapes are sufficient for this prototype.

## Current model preview

![Compact tracked companion: front, side, top, and three-quarter views](src/robot_description/docs/geometry-preview.png)

These views are rendered from the current URDF visuals, not a Gazebo screenshot
or the finished exterior design. The model is approximately **190 x 161 x 120 mm**,
with a **90 mm diameter head**.

## Current development stage

Development currently uses ROS 2 Jazzy and Gazebo Harmonic (Sim 8) on Ubuntu
24.04 in WSL2/WSLg. The repository implements the initial geometry and simulation
foundation: body, fixed track envelopes, a passive head pitch joint, a minimal
world, and ROS joint-state/TF integration.

The tracks do not move yet, and the head has no actuator controller. Movement,
head control, camera and sensor integration, and eventually AI behavior are
development directions from the project brief; they are not implemented product
capabilities. Physical hardware integration is also still ahead.

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
