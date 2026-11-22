# Head pitch control

`robot_head` controls the existing head joint in ROS 2 Jazzy / Gazebo Harmonic.
Angles are relative to the main body: zero looks forward, positive looks up,
negative looks down. Physical hardware is not implemented.

## Run

In WSL Ubuntu 24.04:

```bash
cd /home/george/robot_ws
source scripts/ros_env.sh
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch robot_head head_control.launch.py gui:=true
```

Use `gui:=false` for headless simulation. Source the same environment in a second
terminal. After ROS discovery, send one command at a time:

```bash
ros2 topic pub --once /head/pitch/target std_msgs/msg/Float64 '{data: 0.0}'
ros2 topic pub --once /head/pitch/target std_msgs/msg/Float64 '{data: 0.2617993877991494}'
ros2 topic pub --once /head/pitch/target std_msgs/msg/Float64 '{data: -0.2617993877991494}'
ros2 topic echo /head/pitch/actual
```

Command and actual are radians. +15 degrees is +pi/12 radians; -15 is -pi/12.
The head is a plain sphere, so read measured joint feedback to observe rotation.
The acceptance procedure requires actual pitch within ±2 degrees for three
continuous **simulation** seconds before sending the next target.

## Interfaces and behavior

| ROS topic | Type | Meaning |
| --- | --- | --- |
| `/head/pitch/target` | std_msgs/Float64 | Body-relative upward-positive pitch, radians. |
| `/head/pitch/accepted` | std_msgs/Float64 | Accepted target; not a physical completion acknowledgement. |
| `/head/pitch/actual` | std_msgs/Float64 | Measured upward-positive pitch, derived from actual named joint state. |
| `/joint_states` | sensor_msgs/JointState | Existing raw URDF convention: downward-positive for head_pitch_joint. |
| `/head_pitch_joint/reference` | std_msgs/Float64 | Internal raw downward-positive simulation reference. |

Public Float64 topics use reliable, volatile, keep-last depth-one QoS. Send one
source of commands; the latest valid target replaces its predecessor. Exact
URDF boundaries are accepted; out-of-range and non-finite values are rejected
with a warning and retain the previous target. Startup targets neutral. Command
publisher loss does not return the head to neutral. Actual feedback is emitted
only on a valid measured joint sample; missing/invalid data does not create zero
or timer-repeated fake feedback. `/joint_states` and head TF retain their contracts.

Native Gazebo force PID is the only actuator writer. The generated model derives
position, velocity and effort constraints from the installed description (currently
±0.610865 rad, 1 rad/s and 0.1765 N m). Tunable gains and reference speed scale live
in `config/head_control.yaml`; the scale is bounded by 1 and defaults to
0.17453292519943295 in this launch, giving a 10 degrees/s reference with the
current 1 rad/s joint limit. Reference travel is 1.5 seconds for 15 degrees
and 3 seconds for a 30-degree reversal; actual travel and settling depend on tracking. The URDF axis, geometry and position/velocity constraints are unchanged.
The effort ceiling uses the MG90S 4.8 V stall rating (see below).
The temporary model is retained through launch and deleted on shutdown.

A timestamp rewind preserves the running adapter's last target/reference and
rebases dt. Test fixtures instead invalidate the affected attempt, stop its owned
launch and restart that test from fresh setup within the original finite budget.
A newly started adapter targets neutral. Shutdown sends no new neutral command;
the native PID retains its last received reference while Gazebo remains running.
Active holding after controller termination is not promised.

The optional `model_file:=/absolute/preconfigured.urdf` launch override bypasses
model generation while validating the head constraints. It is useful for testing
an intentionally passive model; the default empty value generates the actuator.
The original `robot_description gazebo.launch.py` remains a passive baseline.

## Verification

```bash
./scripts/check.sh          # unit/ROS/description checks, no Gazebo
./scripts/check.sh --full   # additionally physical Gazebo acceptance
```

Fast coverage includes input limits/sign, reference slew/reset behavior,
configuration, measured feedback, command replacement/publisher loss, and hold/
retry evaluators. Physical coverage includes seven targets/reversals with 3s
holds, exact boundaries, invalid-command recovery, resets during movement/hold,
adapter shutdown, disabled actuator and missing feedback negative proofs, early
exit and SIGTERM cleanup. Each run reserves its ROS domain and Gazebo partition,
records JSON reports/traces under pytest's reported temporary directory, and
cleans up only its owned process group. The suite checks measured body-relative
joint position/velocity; it does not compare body motion against the ground.

The hold timer restarts on an out-of-band/invalid observation. Paused/duplicate
simulation time cannot advance it. Reset attempts cannot share hold evidence or
renew their original budget. No travel-time guarantee is introduced by runner
deadlines. Force saturation is verified through generated SDF configuration and
the native force-PID command path; joint wrench feedback is not mislabeled as
measured actuator torque. See `specs/001-head-control/verification.md` for actual
results, environmental limits and independent review status.

Hold verification derives the expected sample period from the installed world's
physics step (currently 1 ms, matching the Gazebo joint publisher's observed
per-step stream). A missing-step gap clears the hold; recovered feedback must
establish a new full 3 seconds. Invalid or out-of-band values clear the hold even
with a duplicate timestamp. Public actual values and raw measurements are recorded with DDS source timestamps
and receipt order. The verifier matches the adapter's exact sign conversion in
raw-source order and requires the raw publication to precede the actual
publication; this handles independently queued topics without pairing different
moments. Agreement during movement and arrival retains the existing ±2-degree band. Reports retain `actual-*.json`
associations and `source-times-*.json` publication metadata alongside raw traces, and a corrupted/target-echo public-feedback
negative test proves this comparison detects disagreement.

DDS source publication timestamps are used only within a continuous epoch. If
those timestamps rewind, the measurement attempt is invalidated and the affected
test restarts with fresh setup under its original budget, just as for simulation
clock reset. No cross-epoch feedback association is accepted.

## MG90S actuator assumptions

The planned actuator is a TowerPro MG90S. Its [manufacturer specification](https://towerpro.com.tw/product/mg90s-3/)
lists 1.8 kgf cm stall torque at 4.8 V: 0.1765197 N m. The URDF effort
ceiling rounds this down to 0.1765 N m, which also bounds the generated
Gazebo force PID. Stall torque is not a continuous-duty torque rating.
The published 4.8 V speed is 0.10 seconds per 60 degrees (600 degrees/s);
we retain the stricter existing 1 rad/s joint velocity limit.

This is a simplified simulation using a hardware-informed torque ceiling,
not a calibrated MG90S model or a physical servo driver. It does not model
voltage-dependent torque/speed, current, heating, backlash, deadband or a
PWM calibration. The manufacturer's voltage fields are inconsistent, so the
4.8 V figures are the documented basis. Physical load capacity, motion and
angle accuracy remain unverified.
