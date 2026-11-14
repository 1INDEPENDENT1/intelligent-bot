# Tasks: Robot description baseline verification

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md.

## Phase 1: Setup
- [x] T001 Define acceptance criteria and verification mapping in specs/001-robot-description-baseline/spec.md and plan.md; confirm runner limits.

## Phase 2: Foundations
- [ ] T002 Register pytest dependencies and test groups in src/robot_description/CMakeLists.txt and package.xml after test files exist.

## Phase 3: User Story 1 - Fast baseline
**Goal**: Protect installed resources and documented model contracts.
**Independent test**: Run fast pytest against installed assets and broken temporary overlays.
- [ ] T003 [US1] Write resource and model-contract tests in src/robot_description/test/test_description.py; prove missing resource, contract, and limit mutations fail.

## Phase 4: User Story 2 - Runtime baseline
**Goal**: Observe the existing integration in an isolated headless simulation.
**Independent test**: Run the Gazebo test with intact and broken launch/config overlays.
- [ ] T004 [US2] Write the real Gazebo observation and process cleanup test in src/robot_description/test/test_gazebo_smoke.py.
- [ ] T005 [US2] Record missing spawn/clock/joint/TF and cleanup failure-path evidence in specs/001-robot-description-baseline/verification.md.

## Phase 5: User Story 3 - Trustworthy check command
**Goal**: Select fast/full tests and propagate real failures with fresh results.
**Independent test**: Run both modes, invalid input, and an injected failed test.
- [ ] T006 [US3] Extend scripts/check.sh with fast/full modes, registration checks, fresh result handling, and nonzero test-failure status.
- [ ] T007 [US3] Update README.md and src/robot_description/README.md with commands, coverage, dependencies, and exclusions.

## Phase 6: Verification and review
- [ ] T008 Run fast/full checks and negative verification; record evidence and acceptance outcomes in specs/001-robot-description-baseline/verification.md.
- [ ] T009 Request independent reviewer assessment; resolve blockers, rerun affected checks, and record review in specs/001-robot-description-baseline/review.md.

## Dependencies and Execution
T001 precedes all implementation. Write T003/T004 before registration T002.
T006 follows registered tests; T007 follows final runner behavior. T008 precedes
T009. T003 and T004 can be authored independently, but execution is sequential
to avoid shared build/result state. No parallel implementation agents needed.
MVP is US1; deliver all three stories as requested. No commit or push is included.
