# Feature Specification: Robot description baseline verification

**Feature Branch**: `codex/robot-description-baseline`
**Created**: 2026-10-19
**Status**: Specified
**Input**: Implement baseline verification through SDD, avoid redundant checks,
prove that violated expectations fail, run fast and full checks, and obtain an
independent reviewer assessment. Preserve existing robot functionality.

## User Scenarios & Testing

### User Story 1 - Check the installed description (Priority: P1)

As a developer, I can run fast checks before commit and detect broken model
resources or public model contracts without starting a simulator.

**Why this priority**: This protects the model that every later subsystem uses.
**Independent Test**: Run the fast command against a built workspace and against
temporary broken copies of its installed description.

**Acceptance Scenarios**:

1. **AC-01**: Given the current description, conversion succeeds, the workspace
   builds, and installed URDF, launch, world, bridge configuration, and every
   referenced mesh can be located without relying on the working directory.
2. **AC-02**: Given the documented model, its public frames and joints retain
   their documented connectivity and types; the head pitch axis is Y and its
   limits are finite, ordered, with positive effort and velocity.
3. **AC-03**: Given a missing installed resource, broken mesh reference, changed
   joint contract, or invalid joint limits, the corresponding test fails and
   reports the violated condition. Malformed model structure fails conversion.

### User Story 2 - Observe the existing simulation (Priority: P2)

As a developer, I can explicitly run a headless smoke test that proves the
existing Gazebo-to-ROS integration actually produces observable results.

**Why this priority**: Parsing and building alone cannot validate runtime wiring.
**Independent Test**: Run the full command in Ubuntu 24.04 / ROS 2 Jazzy / Gazebo
Harmonic; no GUI or physical robot is required.

**Acceptance Scenarios**:

1. **AC-04**: Headless launch creates `my_robot` in `minimal`; the test observes
   advancing `/clock`, `/joint_states` containing `head_pitch_joint` with a finite
   position, and usable transforms from `base_footprint` to `base_link`,
   `left_track_link`, `right_track_link`, and `head_link`.
2. **AC-05**: If spawning, clock bridging, joint-state publication, or head TF is
   absent, the smoke test fails with the missing observations instead of passing
   merely because launch started. Unexpected launch exit also fails.
3. **AC-06**: Success and failure both clean up the simulation started by the
   test. Existing unrelated processes are not stopped; unrelated simulations
   cannot supply the test's evidence.

### User Story 3 - Trust the check result (Priority: P3)

As a reviewer, I can distinguish fast checks from full runtime verification and
inspect current results rather than stale or empty success reports.

**Why this priority**: The quality gate must communicate what was actually run.
**Independent Test**: Run both modes and a deliberately failing registered test.

**Acceptance Scenarios**:

1. **AC-07**: The default command runs fast checks; full mode additionally runs
   the Gazebo smoke test. Both return nonzero on failure and print accurate
   results; fast mode explicitly states that simulation was not run.
2. **AC-08**: Result reporting excludes previous runs. Tests are registered with
   the package, their failed assertions propagate to the command exit status,
   and a zero-test selection cannot be reported as baseline coverage.

### Edge Cases

- Missing installed files or meshes, renamed frames, disconnected/malformed
  model, wrong joint type, equal/reversed/non-finite limits.
- Simulator or ROS dependency missing, launch exits, model is not created,
  clock does not advance, expected joint/TF never arrives.
- An unrelated simulator is already running; tests must isolate their traffic.
- Previous failing/passing result files, unknown check arguments, test failure
  followed by cleanup, and signal interruption of the check command.

## Requirements

### Functional Requirements

- **FR-001**: Verify AC-01 through AC-03 once at the cheapest reliable level;
  reuse the existing conversion check rather than duplicate parser validation.
- **FR-002**: Verify AC-04 through AC-06 with the real installed launch and real
  Gazebo/ROS observations; do not replace the integration with mocks.
- **FR-003**: Provide the fast/full selection and truthful failure/result
  behavior in AC-07 and AC-08 through the existing check command.
- **FR-004**: Demonstrate negative cases with temporary broken copies, without
  leaving changes to the production URDF, launch, bridge, or world.
- **FR-005**: Record criterion-to-test mapping, commands, actual results,
  limitations, and independent review evidence.

## Success Criteria

- **SC-001**: Every acceptance criterion has an explicit verification method and
  recorded result; both requested modes finish successfully on the baseline.
- **SC-002**: Representative violations of each checked condition produce a
  failed assertion or command, not a silent pass, skip, or zero-test success.
- **SC-003**: Existing robot interfaces and runtime behavior remain unchanged;
  no claims are made about untested physical behavior.

## Assumptions and Boundaries

- Source of current contracts: `src/robot_description/README.md`, URDF, launch,
  world, and bridge configuration. There are no existing feature specifications.
- Existing frames: `base_footprint`, `base_link`, `head_link`,
  `left_track_link`, `right_track_link`. Head is passive; tracks are fixed.
- Excluded: movement/control, hardware, rendering quality, exact geometry
  snapshots, settling/stability tolerances, inertial accuracy, and performance.
- Test-runner limits: 60 seconds wall-clock observation, then up to 10 seconds
  graceful cleanup before forced termination of test-owned processes (user agreed).
  These bound test execution, not robot performance or physical behavior.
