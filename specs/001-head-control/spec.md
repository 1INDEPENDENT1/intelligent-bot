# Feature Specification: Head Pitch Control

**Feature Branch**: `codex/001-head-control`

**Created**: 2026-11-14

**Status**: Specified

**Input**: Create `001-head-control`. Implement vertical head movement in Gazebo
using the existing `head_pitch_joint`. Accept target angles through ROS 2:
0° faces forward, +15° tilts upward, -15° tilts downward. Physically move the
head relative to the body through its joint, expose its actual angle, reach each target within
±2°, respect URDF limits, and preserve existing checks.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aim the head independently (Priority: P1)

As a robot operator, I can command the head to look forward, up, or down
relative to the main body using the existing head joint.

**Why this priority**: Independent head movement is the requested capability.

**Independent Test**: Launch the project simulation, issue targets through ROS 2,
and read the actual simulated head joint angle relative to the body.

**Acceptance Scenarios**:

1. **AC-01**: Given the running simulation, when the operator commands 0°, then
   the head reaches its forward-facing neutral orientation within ±2° and
   remains within that band for 3 continuous seconds of simulation time.
2. **AC-02**: Given neutral head orientation, when +15° is commanded, then the
   head physically tilts upward and reaches +15° within ±2°.
3. **AC-03**: Given neutral head orientation, when -15° is commanded, then the
   head physically tilts downward and reaches -15° within ±2°.
4. **AC-04**: Given a non-neutral position, when the opposite target and then
   0° are commanded sequentially, then the head reverses direction and returns
   to neutral with the same accuracy and 3-second continuous hold for each
   target. Verify both upward-to-downward and
   downward-to-upward transitions.
5. **AC-05**: When a head target is commanded, the actual head joint angle
   changes relative to the body. Tilting or translating the whole robot with
   the head joint unchanged cannot satisfy this test. Body motion relative to
   the ground is outside this feature's acceptance criteria.

---

### User Story 2 - Observe the actual head angle (Priority: P1)

As an operator or ROS 2 client, I can read the actual simulated angle and tell
whether the head has reached the requested orientation.

**Why this priority**: A command alone cannot prove physical movement or accuracy.

**Independent Test**: Observe feedback without sending commands, then compare
feedback during a commanded transition with the simulator-originated joint state.

**Acceptance Scenarios**:

1. **AC-06**: Given a running simulation, when a client subscribes to feedback,
   then it receives finite actual head-position samples with documented units,
   sign convention, and joint identity.
2. **AC-07**: During motion and after arrival, reported actual position comes
   from simulated joint state rather than echoing the target. After conversion
   to the operator convention it agrees with measured body-relative head pitch within
   the same ±2° acceptance band. Existing joint-state and TF consumers remain usable.

---

### User Story 3 - Operate within limits reproducibly (Priority: P2)

As a developer, I can reproduce head control, verify boundary behavior, and
retain the working baseline without physical hardware.

**Why this priority**: Limits and repeatable checks make the increment safe to build on.

**Independent Test**: Exercise both joint boundaries and invalid commands, then
run existing checks and the feature's automated simulation verification.

**Acceptance Scenarios**:

1. **AC-08**: Commands at both URDF position limits are handled as valid
   boundary targets; commanded and measured motion remain within those limits.
   Velocity and effort remain constrained by the existing URDF limits.
2. **AC-09**: Commands beyond either boundary and non-finite values follow
   FR-006 without causing an out-of-limit motion. A subsequent valid command
   remains usable.
3. **AC-10**: Startup, absence of further commands, and controller termination
   follow the documented lifecycle policy in FR-006. A clock reset during a
   test invalidates that attempt and restarts only the affected test from fresh
   setup; pre-reset measurements and hold time cannot contribute to a pass.
4. **AC-11**: A documented launch and command/feedback procedure reproduces the
   capability; existing checks pass and new checks detect wrong direction,
   missing physical motion, missing feedback, and target error above ±2°.

### Edge Cases

- Exact lower and upper limits, and finite values beyond each limit.
- Non-finite target values, including NaN and positive/negative infinity.
- Repeating the current target and returning to zero from either direction.
- A new target while movement is in progress; arbitration behavior must be
  documented in the interface contract before implementation.
- Startup before any target, command publisher disappearance, and shutdown.
- Paused simulation, missing feedback, or simulator failure: verification must
  report missing evidence or failure rather than success from an echoed command.
- Moving the whole model while leaving the head joint unchanged must not count
  as head movement; ground position and body settling are not acceptance metrics.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a target head pitch through a documented
  ROS 2 interface, controlling the existing `head_pitch_joint`.
- **FR-002**: The operator convention MUST be 0° forward, positive upward,
  negative downward, relative to the body. Interface units and conversion to
  the URDF joint convention MUST be explicit and consistent in commands and feedback.
- **FR-003**: Commands 0°, +15°, and -15° MUST cause physical head rotation to
  the corresponding orientation with absolute target error no greater than 2°.
- **FR-004**: For each aiming target, the actual body-relative head angle MUST
  remain within ±2° continuously for 3 seconds of advancing simulation time
  before the target passes. A sample outside the band resets the hold timer;
  re-entry starts a new full 3-second window. Paused/duplicate time and invalid
  or absent measurements cannot establish a hold. No maximum travel-time
  guarantee is required; verification uses the documented bounded wall budget.
  A clock reset invalidates the current attempt and restarts the affected test
  from fresh setup, discarding its observations/hold timer. Other tests are not
  restarted. Retry attempts MUST share a finite original test budget, so repeated
  resets cannot loop forever or be recorded as a pass.
- **FR-005**: Head movement MUST be measured relative to the main body through
  the actual simulated `head_pitch_joint` angle. Head commands MUST actuate that
  joint; moving the whole robot with a fixed head joint is not sufficient. No
  world-frame body-stability tolerance or no-command reference run is required.
- **FR-006**: The system MUST start with a neutral target. It MUST reject finite
  targets outside the URDF range and all non-finite targets, preserving the last
  valid target. While the controller runs, absence or loss of command publication
  MUST retain the last valid target; no command timeout or automatic return to
  neutral is required. Invalid input MUST be observable as rejection through the
  documented interface or diagnostics. Shutdown MUST not issue an unintended
  target or cause uncontrolled motion; controlled holding after the controller
  stops is not required by this simulation increment. A backward clock sample
  alone MUST NOT replace the last accepted target with neutral; it resets timing
  bookkeeping without applying a negative time delta. A new controller started
  by a test restart follows the existing neutral-startup rule.
- **FR-007**: Motion MUST respect the URDF position, velocity, and effort limits;
  limits MUST NOT be widened to make acceptance commands succeed.
- **FR-008**: Actual simulated head angle MUST be exposed through ROS 2,
  distinguishable from the target, with documented units and sign. Preserve the
  existing `/joint_states` and head TF contracts; any operator-sign conversion
  MUST NOT silently redefine standard joint-state semantics.
- **FR-009**: The feature MUST provide reproducible launch, command, feedback,
  and verification instructions and preserve existing model and runtime checks.
- **FR-010**: Before implementation, the plan MUST define command and feedback
  names, message types, units, sign mapping, lifecycle and target replacement
  semantics, subsystem ownership, dependencies, and verification procedures.
  Keep control behavior independent of future physical actuator drivers.

### Key Entities *(include if feature involves data)*

- **Target head angle**: Requested body-relative head orientation; zero neutral,
  positive upward, negative downward; transmitted units documented by the contract.
- **Actual head angle**: Measured simulated orientation, including joint identity
  and sign/units needed to compare it with the target.
- **Joint limits**: Existing URDF position, effort, and velocity constraints;
  converted consistently when using the operator sign convention.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three targets (0°, +15°, -15°) and both direction reversals
  yield the specified body-relative orientation within ±2° continuously for
  3 simulation seconds per target.
- **SC-002**: Nonzero head commands change the actual head joint angle relative
  to the body; whole-model motion with an unchanged head joint cannot pass.
- **SC-003**: Actual-angle feedback remains observable during operation, follows
  measured motion, and demonstrates the same ≤2° target accuracy throughout
  the 3-second acceptance window.
- **SC-004**: Both boundary targets and all invalid-input cases satisfy the
  agreed policy, with no motion beyond the defined joint constraints.
- **SC-005**: Existing automated checks and feature-specific checks pass;
  reproducible evidence demonstrates physical head movement, feedback, and
  body-relative joint motion rather than merely a successful build.

## Assumptions

- This invocation creates the specification, not the implementation or task list.
  The feature directory is explicitly `specs/001-head-control`, as requested,
  even though another feature already uses the numeric prefix `001`.
- Scope is ROS 2 Jazzy / Gazebo Harmonic simulation. Physical hardware drivers,
  head yaw, locomotion, sensors, and autonomous behavior are outside this increment.
- Current source facts: `head_pitch_joint` connects `base_link` to `head_link`,
  axis `0 1 0`, position limits ±0.610865 rad (approximately ±35°), velocity
  1 rad/s, effort 0.1765 N·m (MG90S adjustment, 2026-11-22). Source: `src/robot_description/urdf/robot.urdf`.
- The current +Y joint convention rotates the head's forward +X direction
  downward. The requested upward-positive convention therefore needs explicit
  mapping; retaining existing model and joint-state conventions is preferred.
- `/joint_states` already carries Gazebo joint feedback, and head TF is provided
  by the existing state publisher. Reuse is possible; neither proves actuation today.
- The featureless spherical head cannot reliably demonstrate pitch visually.
  Use simulator-originated joint position as the measured body-relative angle;
  never substitute a target or controller reference for actual joint feedback.

### Verification scope and workflow

| Acceptance criteria | Lowest reliable verification level and observable evidence |
| --- | --- |
| AC-01–04 | Gazebo/system: command each angle and reversal, read actual joint pitch relative to body, compare error with 2°; timing per FR-004. |
| AC-05 | Gazebo/system: confirm the measured head joint angle changes; a locked head joint cannot pass from whole-model motion or a target echo. |
| AC-06–07 | ROS 2 integration for feedback availability/contract; Gazebo-originated JointState comparison for measured-state provenance, sign, and accuracy. |
| AC-08–09 | Unit tests for mapping/validation when separable; Gazebo for limit enforcement and valid-command recovery. |
| AC-10 | ROS 2 integration and Gazebo lifecycle scenarios according to FR-006. |
| AC-11 | `./scripts/check.sh`, `./scripts/check.sh --full`, feature-specific checks, and documented reproduction instructions. |

Planning must make each procedure objectively pass/fail before implementation,
including the bounded observation procedure and the actual joint-angle measurement.
Test infrastructure must use bounded
waits, report missing/stale observations, and clean up only processes it started.
Per AGENTS.md, substantial-feature completion also requires independent review
by the `reviewer` subagent, resolution of blocking findings, and fresh verification
of affected behavior. No hardware check is required for this simulation-only scope;
hardware behavior must not be reported as verified. No constitutional exception
is proposed.

### Clarifications confirmed on 2026-11-14

- Reject out-of-range and non-finite commands; start neutral and retain the last
  valid target while the controller runs, including after command publication stops.
- **Updated on 2026-11-17**: no travel-speed guarantee; target acceptance now
  requires a continuous 3-second in-band hold (see latest clarification below).
- **Superseded on 2026-11-17**: the initial no-command body comparison was
  replaced by head-angle measurement relative to the main body (see below).


### Scope clarification confirmed on 2026-11-17

- The user clarified that head angle is measured relative to the main body.
  Body position relative to the ground is not part of this task. This supersedes
  the 2026-11-14 no-command body-reference choice above.
- Use the existing simulator joint feedback; remove the paired reference run,
  body displacement/rotation comparison, and additional world-pose instrumentation.
- Targets 0°, +15°, -15°, reversals, ±2° target accuracy, URDF limits,
  invalid-input/lifecycle behavior and existing checks remain required.

### Timing and reset clarification confirmed on 2026-11-17

- The user requires 3 continuous seconds within the expected ±2° range before
  passing each target. Use advancing simulation time; pauses cannot count.
- A clock reset invalidates the current attempt and restarts the affected test
  from its setup, without carrying observations or hold time across attempts.
- A reset is a test-restart condition, not an implicit operator neutral command.
  The restarted controller initializes neutral normally; existing controller
  target retention is unchanged by a timestamp rewind alone.


### MG90S settings adjustment confirmed on 2026-11-22

- User selected MG90S as the planned head actuator and requested settings to
  match it; selected a desired commanded reference speed of 10 degrees/s.
- Keep the existing position range and stricter 1 rad/s joint velocity cap.
  Configure the reference slew to 10 degrees/s (15 degrees in 1.5 simulation
  seconds, 30 degrees in 3 seconds); this is not a physical arrival guarantee.
- Use the manufacturer's 4.8 V stall torque as the simulation effort ceiling:
  1.8 kgf cm = 0.1765197 N m, rounded down to 0.1765 N m. This changes the
  previous 0.5 N m limit. No continuous-duty rating is inferred.
- Verify configured reference timing in both directions and reversals with unit
  tests, generated saturation from the installed URDF, and the existing full
  Gazebo acceptance suite (actual within +/-2 degrees for 3 continuous seconds).
- This remains simulation-only; a physical driver, PWM calibration, acceleration
  profile and real-servo load/accuracy validation are outside this adjustment.
