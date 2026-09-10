# Compact tracked companion — geometry prototype

Ubuntu 24.04 (WSL2/WSLg), ROS 2 Jazzy, Gazebo Harmonic / Sim 8.
Based on the supplied engineering reference sheet; no decorative shell,
arms, manipulators, sensors, or AI are included.

## Build and launch

Inside WSL **Ubuntu-24.04**:

    source /opt/ros/jazzy/setup.bash
    cd ~/robot_ws
    colcon build --packages-select robot_description --symlink-install
    source ~/robot_ws/install/setup.bash
    ros2 launch robot_description gazebo.launch.py

For a server without a GUI:

    ros2 launch robot_description gazebo.launch.py gui:=false

Source both setup files in each new terminal. Run one instance at a time.
Stop with Ctrl+C. If a previous Gazebo server remains after closing launch,
close that instance before launching another model in the same world.

For missing dependencies:

    rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy

## Geometry and frames

Units: metres, kilograms, radians. +X forward, +Y left, +Z up.
base_footprint and base_link share the nominal ground origin.

| Item | Prototype geometry |
| --- | --- |
| Overall envelope | 190 x 161.2 x 120 mm (160 mm across belts) |
| Head | Sphere diameter 90 mm |
| Head centre / pitch pivot | x=47 mm, y=0, z=75 mm |
| Central body width | 108 mm |
| Track envelopes | 180 x 25 x 50 mm each |
| Track centres | x=0, y=+/-67.5 mm, z=25 mm |
| Nominal ground clearance under floor | 20 mm |
| Total placeholder mass | 1.35 kg |

The rear electronics bay extends from x=-95 to -3 mm.
Two shaped cheeks flank the sphere and cover the pivot height: their inner
faces are at y=+/-46 mm and their top at the pivot is about z=77.6 mm.
Thus approximately the lower half of the head lies inside the body's envelope,
with a real open cavity beneath the exposed sphere instead of overlapping solids.
The head has no neck. The front retaining lip is lower than the cheek supports.

Head-to-body clearances: cheeks 1 mm, floor 2 mm, rear bay 5 mm,
front lip approximately 3.26 mm. Sphere symmetry preserves these clearances
throughout the head pitch range.

![Geometry preview](docs/geometry-preview.png)

This preview is rendered from URDF visuals, not a Gazebo screenshot.

## Links and joints

    base_footprint
      └─ base_footprint_joint [fixed] → base_link
           ├─ head_pitch_joint [revolute, Y axis, +/-35 deg] → head_link
           ├─ left_track_joint [fixed] → left_track_link
           └─ right_track_joint [fixed] → right_track_link

base_link contains floor, rear bay, front lip, and cheek geometry.
The old left/right wheel joints and caster have been removed.

The two track links are separate mounting envelopes, **not simulated moving
belts**. The visible discs are visual-only geometry. This version has no traction
controller, independently commanded track drive, or cmd_vel interface.
A future track simulation can retain these mounting frames and add roller/belt
links or a Gazebo track controller.

The head joint is passive, damped, and limited; its pivot and inertial origin
coincide with the sphere centre. It is ready for a later actuator/controller.
Pitch is visually indistinguishable on a featureless sphere.

## Physics and ROS integration

- Body collisions are boxes placed outside the head cavity.
- Each track collision is a central box plus two cylindrical ends.
- Head collision is a sphere.
- Body inertia combines approximate box components using the parallel-axis
  theorem; track inertia uses a bounding box; head uses a uniform solid sphere.
  Masses are engineering placeholders, not measured hardware values.
- Cheek and track STL meshes are visual assets only.
- Fixed links may be merged by Gazebo's URDF-to-SDF conversion; ROS TF retains
  their named frames.
- The robot spawns 20 mm above the floor and settles under gravity.
- JointStatePublisher publishes head_pitch_joint to /robot/joint_states.
- The existing YAML bridge provides /joint_states and /clock to ROS.
- robot_state_publisher publishes the head TF and fixed mounting frames.
- package.xml exports the mesh resource path for Gazebo.
- Existing launch, bridge, world, and CMake installation layout are retained.

## Verification

colcon build and gz sdf -p completed successfully.
A clean GUI-enabled launch created my_robot. Live ROS messages contained
head_pitch_joint, its base_link-to-head_link transform, and advancing /clock.
Gazebo reported a level settled pose near z=0.
Mesh review confirmed closed surfaces, consistent normals, positive volume,
and no degenerate triangles.

The previous wheeled package is preserved at:
~/robot_ws/robot_description.before-tracked (contains COLCON_IGNORE).
The original earlier backup also remains at:
~/robot_ws/robot_description.before-gazebo.
