#!/usr/bin/env bash
set -euo pipefail

usage() {
    printf 'Usage: %s [--fast|--full]\n' "$0"
    printf '  --fast (default): conversion, build, installed-model tests\n'
    printf '  --full: fast checks plus headless Gazebo/ROS smoke test\n'
}
if (( $# > 1 )); then
    usage >&2
    exit 2
fi
mode="${1:---fast}"
case "$mode" in
    --fast|--full) ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$repo_root"
source "$repo_root/scripts/ros_env.sh"

printf '\n==> Source ROS 2 Jazzy\n'
# ROS/colcon setup scripts may reference unset optional variables.
set +u
source /opt/ros/jazzy/setup.bash
set -u

printf '\n==> ROS middleware: %s\n' "$RMW_IMPLEMENTATION"
if ! ros2 pkg prefix "$RMW_IMPLEMENTATION" > /dev/null; then
    printf 'Missing ROS middleware package: %s. Install project dependencies with rosdep.\n' "$RMW_IMPLEMENTATION" >&2
    exit 1
fi

printf '\n==> Validate URDF-to-SDF conversion\n'
gz sdf -p src/robot_description/urdf/robot.urdf > /dev/null

printf '\n==> Build workspace\n'
colcon build --symlink-install

printf '\n==> Source workspace setup\n'
set +u
source "$repo_root/install/setup.bash"
set -u

printf '\n==> Verify baseline test registration\n'
ctest --test-dir build/robot_description --show-only=json-v1 | python3 -c '
import json, sys
tests = {test["name"]: test for test in json.load(sys.stdin)["tests"]}
required = {"test_description", "test_runtime_environment", "test_gazebo_smoke"}
missing = required - tests.keys()
if missing:
    sys.exit("Missing baseline test registration: " + ", ".join(sorted(missing)))
labels = {p["name"]: p["value"] for p in tests["test_gazebo_smoke"]["properties"]}
if "gazebo" not in labels.get("LABELS", []):
    sys.exit("Gazebo test must have the gazebo label for fast/full selection")
'

printf '\n==> Clear previous generated test results\n'
colcon test-result --test-result-base "$repo_root/build" --delete-yes

ctest_args=(--output-on-failure --no-tests=error --stop-on-failure)
if [[ "$mode" == --fast ]]; then
    ctest_args+=(-LE gazebo)
    printf '\n==> Run fast registered tests (Gazebo excluded)\n'
else
    printf '\n==> Run all registered tests, including Gazebo\n'
fi
# Let pytest finish simulator cleanup before colcon/CTest exit on interruption.
cancel_dir="$(mktemp -d)"
export ROBOT_DESCRIPTION_TEST_CANCEL_FILE="$cancel_dir/cancel"
interrupted_status=0
request_cancel() {
    if (( interrupted_status == 0 )); then
        interrupted_status="$1"
        printf '\n==> Interrupted; waiting for test cleanup\n' >&2
    fi
    : > "$ROBOT_DESCRIPTION_TEST_CANCEL_FILE"
}
trap 'request_cancel 130' INT
trap 'request_cancel 143' TERM
setsid colcon test --return-code-on-test-failure --ctest-args "${ctest_args[@]}" &
test_pid=$!
while :; do
    test_status=0
    wait "$test_pid" || test_status=$?
    kill -0 "$test_pid" 2>/dev/null || break
done
rm -f -- "$ROBOT_DESCRIPTION_TEST_CANCEL_FILE"
rmdir -- "$cancel_dir"
trap - INT TERM

printf '\n==> Report test results\n'
result_status=0
colcon test-result --verbose || result_status=$?
if (( interrupted_status != 0 )); then
    exit "$interrupted_status"
fi
if (( test_status != 0 )); then
    exit "$test_status"
fi
if (( result_status != 0 )); then
    exit "$result_status"
fi

printf '\nAll %s project checks passed.\n' "${mode#--}"
if [[ "$mode" == --fast ]]; then
    printf 'Simulation was not run; use --full for the Gazebo/ROS smoke test.\n'
fi
