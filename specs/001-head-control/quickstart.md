# Quickstart: Head Pitch Control

This guide validates the implemented `robot_head` package. Actual check results
and independent review status are recorded in [verification.md](verification.md).

## Prerequisites and build

Use Ubuntu 24.04 / ROS 2 Jazzy / Gazebo Harmonic in WSL, with project dependencies
installed. No hardware is needed. In a WSL terminal:

```bash
cd /home/george/robot_ws
source scripts/ros_env.sh
source /opt/ros/jazzy/setup.bash
# If rosdep is available, resolve declared package dependencies:
# rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
./scripts/check.sh
```

Expected: nonempty baseline and head fast-test registrations, successful build and
policy/interface checks. Fast mode excludes Gazebo; it does not prove head motion.

## Launch and observe

```bash
ros2 launch robot_head head_control.launch.py gui:=true
```

For headless operation use `gui:=false`. In additional terminals source the same
project/ROS/workspace environment and inspect:

```bash
ros2 topic echo /head/pitch/actual
ros2 topic echo /joint_states
ros2 run tf2_ros tf2_echo base_link head_link
```

After discovery, send each target separately and observe arrival before continuing:

```bash
ros2 topic pub --once /head/pitch/target std_msgs/msg/Float64 '{data: 0.0}'
ros2 topic pub --once /head/pitch/target std_msgs/msg/Float64 '{data: 0.2617993877991494}'
ros2 topic pub --once /head/pitch/target std_msgs/msg/Float64 '{data: -0.2617993877991494}'
ros2 topic pub --once /head/pitch/target std_msgs/msg/Float64 '{data: 0.0}'
```

Expected public actual angles: neutral, upward +15°, downward -15°, neutral,
within ±0.034906585 rad (2°) continuously for 3 simulation seconds per target.
Raw head joint values have the opposite sign. Leaving the band restarts the
3-second window; do not send the next target until that window passes.
Repeat downward/upward reversal. A plain sphere does not visibly show rotation;
read the actual simulated joint position. This is head pitch relative to the body,
regardless of body orientation or position in the world.

Publish 1.0 rad (outside current range): expect rejection warning, no accepted
target change, and continued last valid motion/holding. Follow with a valid zero
target to demonstrate recovery. A one-shot publisher exits after sending; the
controller must retain its last target. Startup without commands targets neutral.

## Automated physical verification

```bash
./scripts/check.sh --full
```

The head system test records target sequence, reversals, exact URDF
boundaries, invalid-input recovery and lifecycle cases in independent simulations, using
actual Gazebo-originated head joint samples. No body-position comparison or
second reference simulation is required.
See [plan.md](plan.md) for the formulas and all AC-01–11 mappings.

Expected: nonempty feature test results plus baseline results, advancing clock,
fresh measured body-relative angle samples, 3 continuous simulation seconds
within ±2° per target, position/velocity
limits and bounded force configuration. Record actual torque observation limitations explicitly if the
backend does not expose actuator force; verify saturation configuration and its
command path rather than mislabeling joint wrench as commanded effort.

Use inherited runner budgets of 60 wall seconds per observation phase and 10
seconds for graceful cleanup; the test must fail on missing evidence, premature
process exit or deadline. These are test bounds, not a robot speed guarantee.
A target passes only after fresh measured body-relative pitch stays within ±2°
for 3 continuous simulation seconds. Leaving the band or invalid measurement
clears the window. Paused time and stale samples do not advance it. Final neutral's
successful hold ends aiming. Reports retain each window's source timestamps,
actual samples/errors and per-attempt outcomes.

Inject a clock reset during movement and during a partial hold: the affected test
attempt must be recorded as invalidated, torn down and rerun from fresh setup.
No earlier hold time/measurement can count. Other completed tests are not rerun.
All attempts share the original finite case budget; repeated resets exhausting it
fail verification rather than looping or reporting a false pass. The adapter does
not command neutral solely from clock rewind; fresh setup starts a new controller
at neutral normally.

Before completion, demonstrate failure detection using reversed sign, disabled
actuation, removed feedback and >2° synthetic errors in isolated test variants.
Stop only processes owned by the run and prove cleanup on failure/interruption.
Run the independent reviewer required by AGENTS.md and resolve blocking findings.
No hardware acceptance is asserted by these commands.
