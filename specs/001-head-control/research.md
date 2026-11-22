# Research: Head Pitch Control

Date: 2026-11-15. Research resolves design choices; runtime acceptance has not run.

## Control backend

**Decision**: Native Gazebo JointPositionController in force PID mode, with
URDF-derived effort bounds and ROS validation/sign conversion/reference slew.
**Rationale**: Installed gz-sim8 8.11.0 includes the native plugin. Its PID writes
force commands; explicit `cmd_min/max` prevents its much larger default output
range. DART imports SDF joint constraints. Actual limits still require simulation
verification. Avoid the velocity bypass because it bypasses effort PID.
**Alternatives considered**: ros2_control/gz_ros2_control adds controller manager
and hardware-interface setup for one joint. A custom effort plugin duplicates
native functionality. Direct pose changes would fail physical-motion acceptance.

Evidence: read-only research agent inspected the installed versions/plugin and
verified URDF-to-SDF preservation of position ±.610865, velocity1, effort.5.
Primary implementation references:
- [Pinned controller source, gz-sim 8.11.0](https://raw.githubusercontent.com/gazebosim/gz-sim/gz-sim8_8.11.0/src/systems/joint_position_controller/JointPositionController.cc).
- [Pinned DART SDF constraints, gz-physics 7.6.0](https://raw.githubusercontent.com/gazebosim/gz-physics/gz-physics7_7.6.0/dartsim/src/SDFFeatures.cc).
- [DART force command path](https://raw.githubusercontent.com/gazebosim/gz-physics/gz-physics7_7.6.0/dartsim/src/JointFeatures.cc).

## Interfaces and responsibility

**Decision**: `robot_head` package with Float64 radian target/actual topics and
an internal raw command topic bridged to Gazebo Double. Keep `/joint_states`
in raw joint convention. New launch composes existing description launch using
an optional model-file override and generated simulation model.
**Rationale**: Explicit upward-positive user contract avoids changing existing
URDF/TF clients. Geometry remains description-owned; future hardware can keep
the public contract. Native controller does not reject invalid targets, so policy
belongs before the bridge. Limits have one source: the installed URDF.
**Alternatives considered**: Degrees at ROS boundary conflicts with conventional
radian robot state. Reversing joint axis breaks an existing tested model contract.
Embedding control logic in robot_description mixes responsibilities.

ROS bridge support: [Jazzy bridge README and conversion matrix](https://github.com/gazebosim/ros_gz/blob/jazzy/ros_gz_bridge/README.md)
includes Float64/Double. Local existing `config/bridge.yaml` already establishes
one-way Gazebo joint-state and clock bridging. Configure new bridge explicitly
ROS_TO_GZ on the raw command; never add a reverse loop.

## Body-relative measurement (updated 2026-11-17)

**Decision**: Reuse actual Gazebo `head_pitch_joint` feedback on `/joint_states`.
Operator pitch is the negative of the measured raw joint angle. Verify public
feedback conversion and retain existing TF compatibility checks.
**Rationale**: The user clarified that only head movement relative to the main
body is required. A joint position directly measures this rotation, independently
of the target and of whole-model motion. The existing Gazebo JointStatePublisher
and bridge already expose it; disable actuation as a negative proof that target
acceptance alone cannot pass.
**Alternatives removed**: The previous PosePublisher/world-pose reconstruction
and paired no-command simulation added verification for ground-relative body
stability, which the user explicitly excluded. No additional measurement subsystem
is needed. The prior I1 analysis finding is superseded by this scope clarification.

## Test selection and bounds

**Decision**: ament_cmake_python packaging, CTest/pytest labels, 60-second
wall observation budget per phase and 10-second cleanup inherited from baseline.
**Rationale**: `scripts/check.sh` passes CTest arguments and excludes label gazebo
in fast mode. The baseline already defines these runner budgets. Reuse avoids
inventing travel-time requirements. Unit/integration checks cover policy; system
checks prove dynamics. Use isolated ROS domains and unique Gazebo partitions.
**Alternatives considered**: ament_python alone does not share this runner's
CTest label selection. A new product settling deadline is not user-authorized.

## Removed body-stability scope

On 2026-11-17 the user replaced the earlier no-command reference comparison with
head-angle measurement relative to the body. Body settling and world-frame body
translation/rotation are not pass/fail criteria for this feature. This supersedes
the earlier body-stability research decision without changing target ±2° accuracy
or URDF limits. No physical head-control verification has been performed yet.

## Hold acceptance and reset policy (updated 2026-11-17)

**Decision**: The user requires actual pitch within ±2° for 3 continuous seconds
before passing a target; use advancing simulation time. An out-of-band sample
restarts the hold window. A reset invalidates and restarts only the affected test
from fresh setup, with observations and partial hold discarded. Retry attempts
share the original finite case budget derived from existing phase budgets.
**Rationale**: This replaces the earlier first-arrival-only procedure and resolves
I2/U1. No new travel-time guarantee is introduced. A timestamp rewind itself
rebases the adapter's dt bookkeeping without replacing its target/reference;
the runner's new controller starts neutral through ordinary startup.
**Alternatives superseded**: Automatic neutral command on a rewind, carrying
partial holds across a reset, and accepting a single transient in-band sample.
**Verification still required**: brief excursions, <3s versus >=3s, stale/paused
feedback, reset during travel/hold, fresh-attempt success, and repeated-reset
budget exhaustion. These are test designs, not observed runtime results.
