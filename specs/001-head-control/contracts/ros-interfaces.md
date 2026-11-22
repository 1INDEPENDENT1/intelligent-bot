# ROS and Simulation Interface Contract

Contract defined 2026-11-15, updated/implemented 2026-11-17. Runtime verification
and review evidence are recorded in ../verification.md.

## Public ROS interfaces

| Interface | Type | Meaning / QoS |
| --- | --- | --- |
| `/head/pitch/target` | `std_msgs/msg/Float64` | `data`: upward-positive target in radians relative to body. Reliable, volatile, keep-last depth 1. |
| `/head/pitch/actual` | `std_msgs/msg/Float64` | `data`: measured upward-positive angle in radians, `-q` from a valid named raw joint sample. Reliable, volatile, depth 1. |
| `/head/pitch/accepted` | `std_msgs/msg/Float64` | Latest accepted target, not actual position; emitted at startup and on acceptance. Reliable, volatile, depth 1. Used for observation/command scheduling, not a correlated multi-client acknowledgement. |
| `/joint_states` | `sensor_msgs/msg/JointState` | Existing Gazebo feedback, including `head_pitch_joint`, remains in raw URDF convention, radians. Subscribe with sensor-data-compatible QoS. |
| `/clock` | `rosgraph_msgs/msg/Clock` | Existing advancing simulation time drives reference slew; clock subscription must match offered QoS. |
| `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | Existing state publisher transforms unchanged. |
| `/rosout` | `rcl_interfaces/msg/Log` | Warning on rejected input/malformed joint feedback; include reason and joint identity. Startup configuration error terminates node with error. |

No services/actions or custom messages. One target source per robot. If multiple
messages arrive, latest valid message processed by the executor replaces the
previous target, including while in motion. Acceptance does not acknowledge native Gazebo consumption or identify the exact
physics step of actuation. There is no completion acknowledgement,
queue of moves, expiry, or cancellation protocol. Publish only after ROS discovery.

`actual` has implicit joint identity through this dedicated topic. It is not a
replacement for timestamped `/joint_states`; use the latter for synchronization.
Do not manufacture zero actual feedback before a measured sample. Reject a sample
without the named joint, a valid position index or a finite position; do not
republish stale feedback on a timer. Integration tests use raw sample timestamps
and receipt ordering; disappearance of measurement must be detectable by missing
new observations. Velocity/effort arrays need not be present for actual-position
publication, but simulation verification must obtain the required physical evidence.

## Units, signs and validation

- `theta` = operator pitch; `q` = raw URDF pitch. `q = -theta`, `theta = -q`.
- Neutral 0; +15° = +π/12 rad target -> raw -π/12; -15° -> raw +π/12.
- Target tolerance 2° = π/90 rad. Tolerance does not expand the valid input range.
- Parse lower `L`, upper `U`, velocity `V`, effort `E` from the installed
  `head_pitch_joint`; require finite ordered limits with zero inside and positive V/E.
- Valid target iff finite and `L <= -theta <= U`. Operator interval is `[-U,-L]`.
  Exact boundaries accepted; no rounding or clamping of invalid targets.
- Missing or invalid model configuration is a startup error; never use fallback limits.

## Internal simulation interfaces

| Interface | Type / direction | Meaning |
| --- | --- | --- |
| ROS `/head_pitch_joint/reference` | `std_msgs/msg/Float64` | Raw downward-positive reference `q_ref`, rad; internal to simulation adapter. |
| Gazebo `/model/my_robot/joint/head_pitch_joint/0/cmd_pos` | `gz.msgs.Double` | Bridge from raw reference ROS_TO_GZ only; native PID input. |
| Gazebo `/robot/joint_states` | `gz.msgs.Model` | Existing GZ_TO_ROS JointState bridge, unchanged. |

Native PID is the only actuator writer. Do not publish the public upward-positive
target directly to Gazebo. Private interfaces are not a hardware API and may not
be used to bypass policy by supported clients. Physical driver substitution can
retain the public target, accepted and actual topics with different internal wiring.

## State and lifecycle

1. Startup: parse model/config; set target/reference zero; native PID initial zero;
   emit accepted zero. Wait for simulation clock; do not fabricate actual feedback.
2. Valid message: replace target, publish accepted target; current reference
   continues smoothly toward it. Repeating target is valid and idempotent.
3. Advancing clock: `q_ref += clamp(q_target-q_ref, -V*dt, V*dt)`;
   publish current reference. Native PID force saturates at ±E.
4. Invalid input: warning; target and reference unchanged; no accepted publication.
5. Publisher disappearance: retain target and continue control while running.
6. Paused/duplicate clock: no slew advancement. No travel-time guarantee.
7. Clock rewind: retain accepted target/reference, rebase previous clock stamp,
   and do not integrate negative dt or emit an accepted-neutral event merely from
   rewind. Test runner invalidates the attempt and restarts only the affected test
   from fresh setup; its new controller starts neutral normally.
8. Adapter shutdown: stop publishing, no new neutral command. PID retains last
   received reference while Gazebo runs. Full launch shutdown stops owned processes.
   A controller crash/shutdown does not guarantee active holding afterward.

The launch accepts `gui` with the same true/false semantics as the baseline and
uses simulation time. `robot_description/gazebo.launch.py` gains optional
`model_file` with its current URDF as default. `robot_head/head_control.launch.py`
passes generated model and starts head adapter plus command bridge. Gains live in
installed config; URDF is authoritative for limits and force saturation. No
user-adjustable override may widen the authoritative constraints.


## Measurement scope (clarified 2026-11-17)

`head_pitch_joint` position is the head rotation relative to the body. Read this
actual simulator measurement and negate it for operator pitch. Body world pose
is not an acceptance input; no pose-publisher or reference-run interface is needed.

## Test acceptance and clock-reset handling (2026-11-17)

Each target passes after actual measured body-relative pitch remains within ±2°
for 3 continuous simulation seconds. Out-of-band/invalid samples clear the hold;
re-entry starts a new full window. Pauses and stale samples cannot advance it.
A clock reset discards that test attempt's accumulated hold and observations;
restart the affected test from fresh setup within its original finite wall budget.
This is a test-runner rule, not a new public movement command or action protocol.

## Diagnostic model override

Head launch also accepts optional `model_file` (empty by default): a nonempty
preconfigured URDF is validated and passed through instead of generating the
actuator. This supports the passive-model negative proof without editing source
or installed descriptions. The default behavior remains native head actuation.
