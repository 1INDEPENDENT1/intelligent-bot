# Implementation Plan: Head Pitch Control

**Branch**: `codex/001-head-control` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-head-control/spec.md`

## Summary

Add a small `robot_head` ROS 2 package that validates upward-positive pitch
commands, maps them to the existing downward-positive joint convention, and
exposes measured upward-positive feedback. Use Gazebo Harmonic's native
JointPositionController in force-PID mode to physically actuate the existing
joint. Preserve the URDF axis, limits, `/joint_states`, and head TF.

Keep the original description launch usable. A new head-control launch includes
it with an optional simulation-only controller configuration, bridge, and head
adapter. No body anchoring, pose teleporting, joint-axis reversal, or altered
inertia is part of this design. Their introduction would change the acceptance
experiment and require a documented design change.

## Technical Context

**Language/Version**: Python 3.12 for ROS adapter/tests, XML/YAML for model and
configuration, CMake/ament for packaging, Bash for existing runner.

**Primary Dependencies**: ROS 2 Jazzy, Gazebo Harmonic (installed gz-sim 8.11.0,
gz-physics 7.6.0 DART backend), rclpy, std_msgs, sensor_msgs, rosgraph_msgs,
ros_gz_bridge, ros_gz_sim, robot_state_publisher, ament_index_python, launch_ros.
The native controller is supplied by Gazebo; no ros2_control stack or extra pose publisher.
Declare actual package dependencies and verify availability through rosdep.

**Storage**: No persistent runtime storage; installed model/configuration and
JSON verification reports with retained traces/logs.

**Testing**: pytest via ament/CTest; pure mapping/validation/state tests; ROS
integration tests; headless Gazebo system test, label `gazebo`. Existing baseline
checks remain registered. domain_coordinator reserves test domains.

**Target Platform**: Ubuntu 24.04 in WSL2/WSLg; Cyclone DDS project environment.

**Project Type**: ROS 2 robot subsystem with simulation adapter.

**Performance Goals**: actual body-relative pitch within ±2° for 3 continuous
simulation seconds per target; no travel-time guarantee.
Use existing 60-second wall-clock observation and 10-second graceful-cleanup
budgets per independently reported phase, inherited from baseline test procedures.
These are runner bounds, not new robot timing requirements.

**Constraints**: Existing URDF position ±0.610865 rad, velocity 1 rad/s, effort
0.1765 N·m (MG90S at 4.8 V, updated 2026-11-22); actual movement, unmodified body dynamics, raw joint conventions intact.
Acceptance measures head pitch relative to the body using actual joint state.
Body position relative to the ground and hardware behavior are outside this increment.

**Scale/Scope**: One robot, one head pitch joint, one command publisher at a time.
No trajectory action server, arbitration among clients, or physical actuator driver.

## Constitution Check

Pre-research: PASS for planning. The specified scope supplies behavior and
acceptance criteria; contract and measurement choices are resolved below before
implementation. No exception to constitution 1.0.0 is proposed.

Post-design: PASS for design, subject to executing the verification gates during
implementation. This is not a claim of feature completion.

| Principles | Design evidence |
| --- | --- |
| 1–3 Simulation first, independence, shared interfaces | Gazebo first; public radian target/feedback independent of backend; future driver can replace internal raw command bridge. |
| 4–6 Ownership, interfaces first, incremental scope | `robot_head` owns command policy; description owns geometry; contract precedes code; one joint only. |
| 7–8 Observability and conventions | Raw JointState and TF preserved; separate operator feedback; simulator-originated joint measurements. |
| 9–10 Configuration and safety | Read limits from installed URDF; saturate native effort; reject invalid inputs; no command expiry; test physical constraints. |
| 11–12 Simplicity and specification | Native PID instead of custom physics plugin or controller manager; linked spec and design artifacts. |
| 13 Definition of Done | Fast/full checks, per-criterion results, reproduction docs, independent reviewer and limitations recorded before completion. |

## Project Structure

### Documentation (this feature)

```text
specs/001-head-control/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/ros-interfaces.md
└── checklists/requirements.md
```

`tasks.md` is generated later by `$speckit-tasks`.

### Source Code (repository root; planned)

```text
src/robot_head/
├── CMakeLists.txt, package.xml
├── robot_head/                 # pure policy helpers and rclpy adapter
├── scripts/head_pitch_node     # installed executable
├── launch/head_control.launch.py
├── config/head_control.yaml
├── config/bridge.yaml
├── test/test_head_policy.py
├── test/test_head_interfaces.py
├── test/test_head_gazebo.py
└── README.md
src/robot_description/
├── launch/gazebo.launch.py     # optional model-file override, original default
├── urdf/robot.urdf             # source geometry/limits, no convention change
└── test/                      # preserve baseline checks
scripts/check.sh               # retain modes, register nonempty head test coverage
```

**Structure Decision**: Use `ament_cmake_python` plus `ament_python_install_package`
in `robot_head`, an installed executable, and `ament_cmake_pytest`, matching the
workspace's CTest runner. Avoid a pure ament_python package whose test selection
would bypass the runner's Gazebo label selection.

Generate an ephemeral simulation URDF from the installed description during
launch: add the native controller plugin, deriving limits from the
same parsed joint. Pass it to the existing launch through `model_file`; both
spawn and state publisher must use the same file. Retain that temporary file
until launch shutdown and clean it up on failures. Never edit installed assets.
Source config holds gains; generation inserts effort saturation from URDF and
validates all overrides. Description launch defaults to its existing installed
URDF, so existing baseline behavior remains reproducible.

## Control and Lifecycle Design

The ROS adapter owns finite/range validation, last-target state, sign conversion,
and a velocity-bounded reference, all in radians. It emits `/head/pitch/accepted`
on startup and each valid target to distinguish acceptance from actual feedback. On startup target and reference
are zero. On each advancing `/clock` sample, advance raw reference toward the
latest accepted raw target by at most `velocity_limit * simulated_dt`. Publish
that reference on the internal command topic. A backwards clock rebases the
previous timestamp while retaining the accepted target and current reference;
never integrate a negative dt or issue neutral solely because time rewound.
Duplicate stamps do not advance the reference. The test runner separately
invalidates and restarts the affected test when a reset is observed.

Use depth-one reliable volatile command QoS, a single-threaded executor, and
latest accepted message wins. Bridge discovery may lag startup; republish the
current reference on subsequent clock updates. Native `initial_position=0`
provides neutral initialization independently. Invalid messages produce a warning
and no state change. Publishing stops at adapter shutdown; no final neutral command
is sent. The Gazebo PID may retain its last received reference until the simulation
stops. Controlled holding after controller termination is not promised.

Native plugin: `gz-sim-joint-position-controller-system`, class
`gz::sim::systems::JointPositionController`, joint `head_pitch_joint`, index 0,
explicit internal topic, `initial_position=0`, `use_velocity_commands=false`,
`cmd_min=-effort`, `cmd_max=effort`. Use tunable p/i/d gains with integral disabled
initially; tune against simulation, not guessed acceptance tolerances. Lock tested
gains in configuration before completing implementation. Physics receives the
original position/velocity/effort limits; reference slew is an additional protection,
not proof of actual velocity enforcement.

## Verification Mapping and Procedures

| Criteria / requirements | Lowest reliable level and pass evidence |
| --- | --- |
| AC-01–04, FR-001–004 | Gazebo: 0,+15,-15,0,-15,+15,0 degree sequence converted to radians. For every target, fresh measured joint position converted to operator pitch must stay within absolute error ≤π/90 for 3 continuous simulation seconds. |
| AC-05, FR-005 | The actual head joint angle must change relative to the body. A locked head joint or disabled actuator cannot pass using whole-model motion or an echoed target. |
| AC-06–07, FR-008 | ROS integration: missing/short/non-finite JointState does not create valid feedback; valid measured samples map to `-q`. Gazebo: compare with measured raw joint state and exercise a disabled-actuator negative case to reject echoed targets. Baseline TF still usable. |
| AC-08, FR-007 | Unit: URDF-derived mapping and inclusive boundaries, reference slew and saturation generation. Gazebo: commands at exact ±0.610865; sampled position and velocity stay in limits. Verify PID output bounds and force-mode configuration through generated SDF; capture applied joint actuation command if backend exposes it. Never interpret JointState effort as actuator torque without verifying its provenance. |
| AC-09, FR-006 | Unit and ROS integration: exact boundaries accepted; next representable values outside boundaries, NaN, ±infinity rejected without altering last target/reference. Check rejection warning and subsequent valid recovery. Gazebo confirms no invalid-target excursion. |
| AC-10, FR-006 | Integration/system: neutral with no initial publisher, single command followed by publisher exit, repeated current target, replacement while moving, adapter shutdown at nonzero target. No unintended neutral/reset command; limits and observations remain valid. |
| AC-11, FR-009–010 | Installed-package launch/CLI reproduction, `./scripts/check.sh` and `--full`, current-run registration and results; wrong sign, disabled PID, absent feedback and synthetic >2° errors must fail relevant checks. |

### Bounded observation and body-relative angle

Use a fresh head-control simulation per independent case (and a fresh attempt
after a clock reset). Subscribe to the existing `/joint_states`
feedback from Gazebo and locate `head_pitch_joint` by name. Its actual position
`q` is rotation of the head relative to its parent body; operator pitch is `-q`.
No PosePublisher, world-frame body measurements, paired neutral simulation,
matched-step replay, or seed synchronization is required.

Use independent parameter cases for neutral, 0→+15, 0→-15, +15→-15,
-15→+15, +15→0 and -15→0 degrees. Establish any initial pose with the same
3-second hold before the target. For each commanded pose:
1. Publish after discovery and observe ROS policy acceptance. Acceptance alone
   is not evidence that Gazebo has applied the command.
2. Observe finite simulator-originated joint samples with advancing source stamps
   after acceptance. Operator pitch is `-q`; require `abs(-q-target) <= pi/90`.
3. Start the hold window at the first fresh in-band sample. Every valid measured
   sample in the window must remain in band. An out-of-band or invalid sample
   clears the window; re-entry starts a new full 3 seconds. Do not advance the
   hold using wall time, duplicate timestamps, a paused clock, or stale feedback.
   Missing measurement evidence cannot be credited as an observed hold.
   Enforce continuity using the installed world physics-step period, matching
   the current joint publisher's per-step stream. A source-stamp gap larger than
   that period clears the window; validate values before ignoring duplicates.
4. Pass the target at a fresh in-band sample whose simulation stamp is at least
   3 seconds after the uninterrupted window's start. Record the window and errors,
   then command the next target. Final neutral's successful hold ends aiming.

Reuse 60-wall-second observation phases and 10-second graceful cleanup. Deadlines
bound tests, not product travel time. Derive a finite original test-case wall
budget from its scheduled phase budgets; all reset attempts share that budget
and never renew it. Missing feedback/clock, early process exit or inability to
complete a hold within the available budget fails verification. Check joint limits
over all collected samples, including hold/re-entry periods.

On a backward simulation clock or DDS publication source epoch reset, record RESET/INVALIDATED,
discard the affected test attempt's measurements and hold state, stop its owned
launch and recreate that test's setup/controller/observers before replaying its
scenario. Do not restart already completed unrelated tests. Preserve invalidated
attempt logs separately. If repeated resets exhaust the original case budget,
report failure to complete, not a successful retry or skip. A fresh controller
starts neutral by the normal startup contract. The runner's restart rule does not
make a time rewind itself a neutral command in a still-running controller.

US2 compares public actual-angle feedback with simulator-originated raw JointState,
not with the command. Persist source-stamped raw measurements, public actual
DDS source timestamps and observer receipt indices. Match the exact sign conversion
in raw-source order and require raw DDS publication no later than actual DDS
publication. Do not pair by latest observer receipt: topic queues may lag differently.
Compare during movement and arrival within the existing ±2-degree agreement band.
A corrupted/target-echo actual or future-only source match must fail.
ROS head TF remains a compatibility check. Fixed-link
reduction changes the Gazebo parent name to `base_footprint`; the URDF body frame
has a fixed zero-rotation transform to it, so the joint remains body-relative.
No world-pose reconstruction is needed. The baseline bridge/publisher must remain
the sole raw joint-state source in the system test; disabled actuation must fail
nonzero target verification even if command acceptance works.

### Implementation gates

1. Prove policy logic with focused tests, then implement adapter and installed resources.
2. Verify generated URDF-to-SDF preserves limits, names, plugin mode and saturation.
3. Measure real PID body-relative joint motion and velocity before polishing
   integration. Tune configurable gains; never broaden limits or introduce slack.
4. Retain baseline tests, register head fast and Gazebo tests with CTest labels;
   extend runner registration checks to reject missing/empty head test coverage.
5. Run fast/full checks; document exact results, failure/negative evidence and
   unverified behavior. Request the `reviewer` subagent, resolve blocking findings,
   and reverify affected behavior before declaring the feature complete.

## Complexity Tracking

No constitutional violations. Native PID plus a small ROS policy adapter avoids
custom physics control and controller-manager infrastructure. Simulation-only
model generation preserves the baseline launch. Existing simulated joint feedback
is sufficient to verify body-relative head movement.



Scope updated 2026-11-17: head pitch relative to body only, continuous 3-second
in-band target acceptance, affected-test restart on clock reset with bounded
attempts. These user decisions supersede analysis findings I1, I2 and U1;
implementation and runtime verification remain pending.

Implementation ruling (2026-11-18): make targets/reversals separate pytest cases,
and split boundary checks from publisher-loss/shutdown. This preserves every
acceptance condition while making the user's affected-test-only restart useful
when the environment corrects DDS wall time more often than a long sequence can
complete. No target, hold duration, source-causality rule or tolerance is relaxed.


## MG90S configuration adjustment — 2026-11-22

Small configuration change under constitution section 12; no new subsystem.
Use the existing URDF-authoritative force ceiling and existing reference slew.
Set head effort to 0.1765 N m (4.8 V MG90S stall specification, rounded down)
and launch reference_speed_scale to 0.17453292519943295 for the user-selected
10 degrees/s with the retained 1 rad/s velocity limit. Keep PID gains, joint
geometry/position limits and ROS contracts. Raising the simulated velocity to
MG90S's published 600 degrees/s would oppose the user's slower-motion request;
a detailed electrical/servo model needs measured hardware data.

Verification: first observe a failing installed-limit regression and both
configured-speed direction cases, then apply settings and run fast/full project
checks. Existing physical cases retain +/-2 degree / 3-second holds, finite reset
budgets, boundary/lifecycle/negative checks and measured feedback provenance.
Published stall torque is a ceiling only, not continuous-duty validation.
Source: https://towerpro.com.tw/product/mg90s-3/ (checked 2026-11-22).
