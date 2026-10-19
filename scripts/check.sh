#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$repo_root"

printf '\n==> Source ROS 2 Jazzy\n'
# ROS/colcon setup scripts may reference unset optional variables.
set +u
source /opt/ros/jazzy/setup.bash
set -u

printf '\n==> Validate URDF-to-SDF conversion\n'
gz sdf -p src/robot_description/urdf/robot.urdf > /dev/null

printf '\n==> Build workspace\n'
colcon build --symlink-install

printf '\n==> Source workspace setup\n'
set +u
source "$repo_root/install/setup.bash"
set -u

printf '\n==> Run registered tests\n'
colcon test

printf '\n==> Report test results\n'
colcon test-result --verbose

printf '\nAll project check commands passed.\n'
printf 'Review the test count above: zero tests does not verify robot behavior.\n'
