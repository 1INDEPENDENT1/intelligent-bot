# Implementation Plan: Robot description baseline verification

**Branch**: `codex/robot-description-baseline` | **Date**: 2026-10-19
**Spec**: [spec.md](spec.md)

## Summary
Keep the existing URDF conversion check. Register two fast pytest tests for
installed resources and model contracts, and one Gazebo smoke test. Extend
`scripts/check.sh` with default fast and explicit `--full` modes. Do not
change production URDF, launch, world, or bridge behavior.

## Technical Context
- Python 3.12, Bash, CMake/ament; Ubuntu 24.04 WSL2, ROS 2 Jazzy, Gazebo Harmonic.
- Use installed pytest/ament_cmake_pytest, rclpy, tf2_ros, domain_coordinator and
  existing ROS messages; declare test dependencies. No new runtime subsystem.
- CTest label `gazebo` selects the system test. Bare `colcon test` runs all.
- Keep simulator and ROS observations in one integration test to avoid repeated
  launches and duplicate checks of bridge source text.
- User-approved observation deadline: 60 wall-clock seconds. Graceful cleanup:
  10 seconds, then force-stop only the test's process group. These are runner
  limits, not real-time robot requirements.
- Use a reserved ROS test domain and unique Gazebo partition. Start launch in a
  separate process group; cleanup in a finally block on pass, failure, interruption.
- Retain logs for diagnosis via pytest/ament and a recorded verification report.
- No geometry tolerances, motion performance, or hardware criteria are introduced.

## Constitution Check
Before and after design: PASS. Simulation first and hardware independence are
preserved. Existing public interfaces remain unchanged. Verification is observable;
fast checks cover static contracts and one system test covers runtime integration.
No new packages, controller logic, abstractions, or constitution exceptions.

## Verification Mapping
| Criterion | Level and method | Negative proof |
|---|---|---|
| AC-01 | Existing conversion/build; installed-resource pytest | Missing installed file/mesh; malformed URDF conversion |
| AC-02 | Model-contract pytest against documented expected relations | Wrong parent/type/axis/frame, invalid limits |
| AC-03 | Temporary broken package overlays run through real pytest | Assert nonzero exit and specific failed condition |
| AC-04 | Real headless Gazebo test; model query, clock, joint-state subscriber, TF buffer | Disable spawn/bridge/publisher in temporary overlay |
| AC-05 | Same test and wall-clock deadline; early launch-exit assertion | Missing runtime observations and early exit |
| AC-06 | Process-group cleanup and traffic isolation | Failed smoke run and interruption; verify no owned live processes |
| AC-07 | Fast/full command execution and argument/failure checks | Invalid mode; injected failing package contract |
| AC-08 | Current-run results, CTest no-tests error, test exit propagation | Stale-result cleanup and missing/failed registration |
| FR-005 | This mapping, verification.md, independent review | Review unsupported claims explicitly |

## Project Structure
- `src/robot_description/test/test_description.py`: two fast installed-package tests.
- `src/robot_description/test/test_gazebo_smoke.py`: one real runtime smoke test.
- `src/robot_description/CMakeLists.txt`, `package.xml`: registration/dependencies.
- `scripts/check.sh`: mode selection, clear output, fresh results, failure propagation.
- Root and package READMEs: commands, coverage, dependencies, limitations.
- `specs/001-robot-description-baseline/`: spec, plan, research, data-model,
  contracts/check-command.md, quickstart, tasks, verification and review records.

## Implementation Strategy
Write assertion-based tests first. Prove negative cases with isolated copies of
installed assets, keeping source intact. Register them, then extend the runner.
Use colcon's result cleanup to avoid stale results and preserve test failure status
while still printing diagnostics. Require at least the expected baseline CTest
registrations, and CTest's error-on-no-tests behavior. Run fast then full checks,
record exact results, and request an independent read-only reviewer assessment.

## Complexity Tracking
No constitutional violations. The sole test process helper is test-local.
