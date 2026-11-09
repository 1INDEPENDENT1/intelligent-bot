# Baseline verification
Inside Ubuntu 24.04 WSL, with ROS 2 Jazzy and Gazebo Harmonic installed:

```bash
cd ~/robot_ws
./scripts/check.sh            # fast, no simulator
./scripts/check.sh --full     # fast + one isolated headless simulation
```

Build/test dependencies are declared in the package manifest; use the repository's
existing rosdep installation procedure on a fresh machine.

Expected: conversion/build success, nonzero fast test count, and one additional
Gazebo test in full mode. Fast output must state that simulation was not run.
See [contracts/check-command.md](contracts/check-command.md) for failure semantics
and [plan.md](plan.md) for acceptance mapping.

Run from another directory using the absolute script path to confirm cwd independence.
Negative verification uses temporary copied installed-package overlays so malformed
models, missing resources, changed contracts and disabled runtime outputs cannot
damage the source. Capture the failed assertion and exit status, then run the intact
baseline. Keep concrete command/results with the run evidence; a verification.md
report can be added when the remaining acceptance matrix has been completed.

The 60-second deadline bounds observations, with up to 10 seconds for graceful
simulator cleanup before forced termination. It does not bound ROS initialization,
shutdown, final reaping, or the complete build/check command. INT/TERM requests to
the check script wait for cooperative test cleanup; an active model query can
consume its remaining observation deadline before cancellation is handled.

Current middleware: the project selects Cyclone DDS (`rmw_cyclonedds_cpp`) through
`scripts/ros_env.sh`, sourced automatically by the check command. Manual ROS
terminals must source that file as described in the
[package README](../../src/robot_description/README.md#build-and-launch).
Two consecutive full project checks passed with Cyclone DDS on 2026-11-06.
Earlier Fast DDS discovery/delivery failures remain unexplained. Those successful
launches do not establish completion of every negative-case verification task.
See the package README for current middleware validation and limitations.

These checks do not establish rendering quality, physical realism, settling
tolerances, actuator behavior, traction, or hardware operation.
