# Tasks: Head Pitch Control

**Input**: Design documents in `specs/001-head-control/`.
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [ROS contract](contracts/ros-interfaces.md),
[quickstart.md](quickstart.md), `.specify/memory/constitution.md`, and `AGENTS.md`.
**Tests**: Required by the specification and project workflow. Write each behavioral
test first, observe its relevant failure, then implement and verify the behavior.
**Status**: All33 implementation tasks completed. Final automated gates and
independent source/evidence review passed; limitations are recorded in verification.md.

## Format and Path Conventions

Tasks use `- [ ] Tnnn [P?] [USn?] description with repository-relative paths`.
`[P]` identifies work on separate files that can overlap after its stated
prerequisites. It does not authorize simultaneous edits to shared files or imply
that simulations sharing a workspace/environment can run safely together.

Use ament_cmake_python and CTest, native Gazebo force PID, upward-positive public
radians, unchanged raw URDF conventions, and the existing URDF as the limit source.
Measure head pitch relative to the body using the existing simulated joint state.
No body/ground stability comparison, extra pose publisher or reference run is required.
Keep assertions focused and Arrange–Act–Assert; fixtures own process management.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the package and test entry points without claiming behavior.

- [X] T001 Create `src/robot_head/package.xml`, `src/robot_head/CMakeLists.txt`, and `src/robot_head/robot_head/__init__.py` using ament_cmake_python, installed scripts/resources and ament_cmake_pytest; declare runtime/test dependencies from plan.md, including actual Gazebo observation dependencies, and check rosdep resolution.
- [X] T002 [P] Create `src/robot_head/config/bridge.yaml` for ROS `/head_pitch_joint/reference` Float64 to Gazebo `/model/my_robot/joint/head_pitch_joint/0/cmd_pos` Double, ROS_TO_GZ only; preserve the existing clock and joint-state bridge in `src/robot_description/config/bridge.yaml`.
- [X] T003 [P] Establish isolated fixtures in `src/robot_head/test/conftest.py`: reserved ROS domain, unique Gazebo partition, Cyclone environment, measured `head_pitch_joint` sample collection, current-run logs/reports, 60-wall-second bounded observation phases, 10-second graceful cleanup, and affected-test restart on clock reset with fresh setup and discarded observations/hold state; derive a finite original case budget from phase budgets and share it across attempts; adapt baseline process ownership/cancellation behavior without stopping unrelated processes.

**Checkpoint**: Package/resources install; fixtures can clean up an intentionally failed run.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Resolve model inputs and baseline-launch compatibility before story implementation.

- [X] T004 Write failing model/configuration tests in `src/robot_head/test/test_head_policy.py` for installed-URDF loading, invalid/missing joint data, preservation of names/axis/connectivity, and generated force-mode saturation; quote constraints from data-model.md: "finite ordered position limits include zero; V/E positive" and "force output bounds derived from ±E; velocity bypass disabled"; reject configuration overrides that widen limits.
- [X] T005 Implement URDF/config loading in `src/robot_head/robot_head/model.py` to satisfy T004 loading tests: `head_pitch_joint` is authoritative, operator limits `[-U,-L]`, missing/invalid configuration terminates startup without fallback limits; read gain configuration without hardcoding geometry or actuator limits.
- [X] T006 Write launch-regression tests in `src/robot_description/test/test_description.py` for default model preservation and optional model_file use by both spawning and robot_state_publisher; verify the original installed description still launches without head actuation.
- [X] T007 Add optional model_file handling to `src/robot_description/launch/gazebo.launch.py` and satisfy T006 while retaining original URDF/gui defaults, public frame contracts and package resource lookup.

**Checkpoint**: Shared input loading passes its focused tests;
baseline launch contract is preserved. Generated force-model assertions in T004
remain red until T013 and must not be hidden or marked passed.

## Phase 3: User Story 1 — Aim the Head Independently (Priority: P1, MVP)

**Goal**: Command physical neutral/up/down movement independently of the body.
**Independent Test**: Read actual simulator-originated head joint feedback to
verify 0°, +15°, -15°, both reversals and ±2° accuracy relative to the body in one
simulation. This does not depend on US2's new public actual-angle topic.

### Tests First

- [X] T008 [P] [US1] Add failing mapping/reference tests in `src/robot_head/test/test_head_policy.py` for operator `q=-theta`, zero initialization, replacement and repeated targets, advancing/duplicate/rewound clocks; preserve exact constraints "Starts zero; advance toward q by at most V*dt per advancing simulation sample. Clock rewind rebases time without changing target/reference. Never beyond [L,U]."
- [X] T009 [P] [US1] Write failing command-interface tests in `src/robot_head/test/test_head_interfaces.py` for Float64 radians, reliable/volatile depth-one QoS, `/head/pitch/accepted`, raw reference sign and rediscovery publication; acceptance acknowledges ROS policy only, not native Gazebo consumption.
- [X] T010 [P] [US1] Add failing body-relative aiming scenarios in `src/robot_head/test/test_head_gazebo.py`: parameterize neutral and transitions 0→+15, 0→-15, +15→-15, -15→+15, +15→0, -15→0 degrees (including verified initial holds), and read actual Gazebo-originated `head_pitch_joint` position q; require fresh `abs(-q-target) <= pi/90` continuously for 3 simulation seconds at every target and joint-angle changes for nonzero moves. Test that just under 3 seconds cannot pass, exactly 3 seconds can pass, a brief out-of-band excursion clears the hold, re-entry starts a full new window, and paused/duplicate time or stale/invalid samples cannot credit a hold. A disabled or fixed joint cannot pass through target echoes or whole-model movement (AC-01–05).

### Implementation and Verification

- [X] T011 [P] [US1] Implement pure command/reference state in `src/robot_head/robot_head/policy.py` to satisfy T008: "Finite and inclusive limits. Starts zero. Latest accepted value replaces previous target. Invalid input leaves it unchanged." Validate before state mutation and apply slew in simulation time.
- [X] T012 [US1] Implement command/clock callbacks and diagnostics in `src/robot_head/robot_head/head_pitch_node.py` and installed `src/robot_head/scripts/head_pitch_node`: parse model, initialize neutral, publish accepted targets and internal reference, retain target on publisher loss, single-threaded latest-valid behavior, no final neutral publication on shutdown; satisfy T009 after T011.
- [X] T013 [P] [US1] Implement ephemeral simulation-model generation in `src/robot_head/robot_head/simulation_model.py`: native JointPositionController index0/initial0/force mode with URDF-derived ±effort bounds and configurable gains; reuse existing JointStatePublisher/bridge, preserve geometry/axis/limits and satisfy remaining T004 assertions, including URDF-to-SDF inspection. No PosePublisher is required.
- [X] T014 [US1] Compose `src/robot_head/launch/head_control.launch.py` with adapter, generated model_file and command bridge; retain the generated file through launch and clean it on normal exit, failed startup and interruption; verify GUI and headless modes using the normal running simulation without reference replay or synchronized stepping; implement the test hold-state helper in `src/robot_head/test/conftest.py` against T010 cases before tuning/verification.
- [X] T015 [US1] Tune force-PID gains in `src/robot_head/config/head_control.yaml` using physical traces from T010, initially with integral disabled; retain original ±0.610865 rad, 1 rad/s and 0.5 N·m constraints, record tested gains and observations in `specs/001-head-control/verification.md`, and never substitute velocity-bypass control or body anchoring to pass.
- [X] T016 [US1] Run US1 focused tests and original baseline checks; record AC-01–05 target, actual body-relative joint angle, error, source timestamp, arrival/deadline outcome and cleanup in `specs/001-head-control/verification.md`. End each target phase only after a continuous 3-simulation-second measured hold within ±2°; finish after final neutral hold. Do not use a ground-position criterion.

**Checkpoint**: A demonstrated physical aiming increment with evidence for AC-01–05.
The complete feature still needs US2, US3 and final quality gates.

## Phase 4: User Story 2 — Observe the Actual Head Angle (Priority: P1)

**Goal**: Expose measured upward-positive feedback while preserving raw consumers.
**Independent Test**: Feed known named JointState samples into the adapter without
sending commands; observe actual=-q and no fabricated/stale outputs. Then compare
actual feedback with simulator-originated raw joint position during a real transition.

### Tests First

- [X] T017 [P] [US2] Add failing feedback tests in `src/robot_head/test/test_head_interfaces.py` for named-joint/index/finite validation, sensor-data-compatible input QoS, public actual Float64 radians and raw conventions; quote "Public actual=-q. No target-derived measurement; malformed/missing samples produce no actual output." Verify missing/short/non-finite samples and absence of measurement do not produce timer-repeated actual output (AC-06).
- [X] T018 [P] [US2] Extend `src/robot_head/test/test_head_gazebo.py` with failing AC-07 comparisons of public actual feedback against simulator-originated raw JointState converted to body-relative operator pitch during transition and arrival, plus existing base_link-to-head_link TF compatibility; disabled actuation must not pass from a target echo.

### Implementation and Verification

- [X] T019 [US2] Add measurement conversion/validation helpers to `src/robot_head/robot_head/policy.py` using only the valid named actual joint sample; preserve source-stamp association for verification and do not require optional velocity/effort arrays to publish actual position.
- [X] T020 [US2] Add `/joint_states` subscription and `/head/pitch/actual` publication to `src/robot_head/robot_head/head_pitch_node.py`, with malformed-feedback warnings and no zero fabrication or target-derived output; satisfy T017 without changing raw JointState or TF semantics.
- [X] T021 [US2] Run standalone feedback and real Gazebo joint-state comparisons for AC-06–07; record measured raw samples, public actual conversion and TF evidence in `specs/001-head-control/verification.md`, confirming US1 body-relative direction and ±2° target accuracy still pass.

**Checkpoint**: Feedback can be verified without commanding movement and accurately
reflects the physical head during commanded operation.

## Phase 5: User Story 3 — Operate Within Limits Reproducibly (Priority: P2)

**Goal**: Prove boundary, invalid-input, lifecycle and regression behavior.
**Independent Test**: Run boundary and lifecycle scenarios directly against the
installed head launch, then fast/full project checks; inspect separate results
rather than accepting a successful build or an empty test run.

### Tests First

- [X] T022 [P] [US3] Extend `src/robot_head/test/test_head_policy.py` and `src/robot_head/test/test_head_interfaces.py` with failing exact-boundary acceptance, next-representable out-of-range and NaN/±infinity rejection/recovery tests; invalid values leave last target/reference unchanged, warn and emit no accepted publication; verify startup error on invalid/missing model, single-command publisher exit, target replacement, duplicate/paused clock, rewind preserving the existing target/reference while rebasing dt, and shutdown without an unintended target (AC-09–10).
- [X] T023 [P] [US3] Extend `src/robot_head/test/test_head_gazebo.py` for both exact URDF boundaries, all invalid cases followed by valid recovery, neutral startup, publisher disappearance, replacement while moving, nonzero adapter shutdown and whole-launch shutdown; inject clock reset during travel and during a partial 3-second hold, require an invalidated attempt followed by fresh setup/replay of only the affected test, and prove the new attempt completes its own full hold without pre-reset credit; require "raw positions within [L,U], absolute velocity <= V; force PID output bounded by E. Record all sampled violations, including after first target arrival" (AC-08–10).

### Implementation and Verification

- [X] T024 [US3] Resolve any policy/interface defects exposed by T022 in `src/robot_head/robot_head/policy.py` and `src/robot_head/robot_head/head_pitch_node.py`; preserve contract behavior and previously passing tests rather than weakening assertions to match implementation.
- [X] T025 [US3] Execute T023, correct any model/launch/gain defects in `src/robot_head/robot_head/simulation_model.py`, `src/robot_head/launch/head_control.launch.py` and `src/robot_head/config/head_control.yaml`, and record AC-08–10 in `specs/001-head-control/verification.md`; inspect converted limits/force saturation and controller command path, capture applied actuation when available, and explicitly report unavailable torque evidence rather than interpreting a joint wrench as actuator torque.
- [X] T026 [US3] Register nonempty head policy/interface and gazebo-labelled physical tests in `src/robot_head/CMakeLists.txt` and strengthen `scripts/check.sh` registration checks while retaining all baseline tests, fast/full selection, fresh results, failure propagation and cancellation cleanup (AC-11).
- [X] T027 [US3] Prove the relevant verifiers fail for isolated wrong-sign, disabled-actuator, missing-feedback and synthetic >2° error variants in `src/robot_head/test/test_head_gazebo.py` and `src/robot_head/test/test_head_interfaces.py`; whole-model motion with a fixed joint cannot pass. Prove early simulator exit, paused/missing clock, short/interrupted holds, stale feedback, cross-reset hold accumulation and repeated resets exhausting the original finite budget cannot pass and clean up owned processes; retain negative evidence in `specs/001-head-control/verification.md`.
- [X] T028 [US3] Run `./scripts/check.sh` and `./scripts/check.sh --full` with installed resources, confirm head tests actually execute, and record separate AC-08–11 outcomes, any failures/skips, registration/count evidence and cleanup in `specs/001-head-control/verification.md`.

**Checkpoint**: Boundary, lifecycle and failure-detection evidence exists with
baseline behavior intact. No hardware behavior is claimed.

## Phase 6: Polish and Cross-Cutting Quality Gates

**Purpose**: Make the implemented capability reproducible and independently reviewable.

- [X] T029 [P] Update `src/robot_head/README.md`, `src/robot_description/README.md` and root `README.md` with installed launch/command/feedback instructions, signs/units, retained-target/rejection policy, test coverage and limitations; reconcile `specs/001-head-control/quickstart.md` with actual commands and artifact/report locations.
- [X] T030 Execute the final `specs/001-head-control/quickstart.md` using installed assets, verify GUI and headless reproduction, reuse unchanged T028 gate results or rerun `./scripts/check.sh` and `./scripts/check.sh --full` if subsequent code changes require it, and complete the AC-01–11 / FR-001–010 evidence matrix in `specs/001-head-control/verification.md`; report failed/skipped/unavailable checks without masking independent results.
- [X] T031 Request the independent read-only `reviewer` subagent required by AGENTS.md to compare implementation, spec, plan and actual evidence; record findings and verdict in `specs/001-head-control/review.md`, including body-relative joint measurement, torque limitations and unverified behavior.
- [X] T032 Resolve all blocking reviewer findings in affected files such as `src/robot_head/robot_head/head_pitch_node.py`, `src/robot_head/robot_head/policy.py`, `src/robot_head/robot_head/simulation_model.py` or `scripts/check.sh`, rerun affected verification and required gates after implementation changes, and update `specs/001-head-control/review.md` and `specs/001-head-control/verification.md`; retain any non-blocking findings and do not declare completion if required evidence/review is unavailable.
- [X] T033 Reconcile completed-task markers in `specs/001-head-control/tasks.md` only with performed work, append material decisions/results/limitations to root `memory.md`, run `git diff --check`, and deliver the final status with remaining non-blocking findings and unverified behavior explicitly stated.

## Dependencies and Execution Order

- Setup T001–T003 precedes foundation T004–T007.
- T004 tests precede T005 model loading and T013 generation; T006 regression
  tests precede T007 baseline-launch changes. Generated-model assertions remain
  red until T013 and must not be misreported as passing in the foundation.
- US1: T008–T010 tests precede T011 policy, T012 node and T013 model generation.
  T014 launch requires T002, T007, T012 and T013. T015 tunes the physical controller;
  T016 verifies body-relative movement and records evidence.
- US2: T017–T018 tests precede T019–T020 measurement implementation; T021 verifies.
  Standalone feedback tests need no command; system comparison requires US1 launch.
  Serialize changes to shared policy/node/test files after US1.
- US3: T022–T023 tests precede T024–T025 fixes, T026 runner registration,
  T027 negative proofs and T028 fast/full gates.
- T029 documentation may overlap T027–T028 without editing their source files.
  T030 reproduction, T031 independent review, T032 fixes/reverification and
  T033 final record follow sequentially.
- Run check.sh serially; never share mutable build/result directories across runs.

## Parallel Examples by User Story

| Story | Safe work after prerequisites | Boundary |
| --- | --- | --- |
| US1 | T008 policy tests, T009 ROS tests and T010 system tests use separate files; later T011 policy and T013 model generation can overlap. | Tests precede implementation; launch/tuning/verification require integrated components. |
| US2 | T017 ROS feedback tests and T018 Gazebo feedback tests use separate files. | Serialize policy/node edits after US1; physical validation requires running launch. |
| US3 | T022 unit/ROS boundary cases and T023 physical cases use separate files. | Fixes and final runner executions follow failing evidence and remain serial where files overlap. |

Parallel examples are optional scheduling choices, not a requirement to spawn agents.

## Acceptance and Requirement Coverage

| Criteria | Tasks | Observable result |
| --- | --- | --- |
| AC-01–04; FR-001–004 | T008–T016 | Commands and reversals produce measured body-relative joint pitch within ±2°, using fresh samples, 3-second continuous holds and bounded waits. |
| AC-05; FR-005 | T010, T016, T027 | Actual head joint angle changes; fixed-joint/disabled-actuator or target-echo cases cannot pass from whole-model motion. |
| AC-06–07; FR-008 | T017–T021 | Public actual follows measured raw joint position with the documented sign; raw JointState and TF remain compatible. |
| AC-08; FR-007 | T004–T005, T013, T015, T023, T025 | URDF-derived constraints and actual position/velocity boundary traces; force evidence explicitly qualified. |
| AC-09–10; FR-006 | T008–T009, T011–T012, T022–T025 | Rejection/recovery, startup, retained target, replacement, shutdown and affected-test restart on clock reset. |
| AC-11; FR-009–010 | T001–T003, T006–T007, T026–T032 | Reproducible installed launch, nonempty fast/full/negative evidence, docs and review. |

## Implementation Strategy

1. Build foundation, then US1: 0°, +15°, -15° and reversals measured at the
   simulated head joint relative to the body, with ±2° target accuracy.
2. Add US2 measured operator feedback and prove it follows actual joint state.
3. Complete US3 limits/lifecycle/negative tests and existing fast/full gates.
4. Finish documentation and independent review. All tasks remain required for
   full completion, and none is marked complete by this documentation update.

Scope clarified 2026-11-17: measure head pitch relative to the body, require a
continuous 3-simulation-second hold within ±2° per target, and invalidate/restart
the affected test after a clock reset. Retry attempts share the original bounded
case budget. Ground-position comparison stays removed. The previously reported I1/I2/U1 design
issues have aligned decisions; actual implementation evidence and reviewer
findings are recorded in verification.md and review.md.


## MG90S settings follow-up — 2026-11-22

These follow-up tasks supersede T015's original numeric effort/reference settings;
completed 2026-11-18 verification remains historical evidence for those settings.

- [X] T034 Update the current spec/plan with MG90S 4.8 V torque basis and the user-selected 10 degrees/s reference; retain position/velocity bounds and ROS contracts.
- [X] T035 Observe failing torque/configured-speed regressions, adjust URDF/config and document hardware-model limitations in package READMEs.
- [X] T036 Run fast/full project checks on the adjusted settings, resolve failures and record actual results and remaining limitations in verification.md and memory.md.
