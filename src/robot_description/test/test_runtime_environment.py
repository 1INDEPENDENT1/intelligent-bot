"""Project RMW selection is exported to child processes and reproducible."""
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("selected, expected", [
    (None, "rmw_cyclonedds_cpp"),
    ("", "rmw_cyclonedds_cpp"),
    ("rmw_fastrtps_cpp", "rmw_fastrtps_cpp"),
])
def test_rmw_selection_reaches_child_process(selected, expected):
    env = dict(os.environ)
    env.pop("RMW_IMPLEMENTATION", None)
    if selected is not None:
        env["RMW_IMPLEMENTATION"] = selected

    result = subprocess.run(
        ["bash", "-c", 'source "$1" && python3 -c '
         "\"import os; print(os.environ['RMW_IMPLEMENTATION'])\"",
         "bash", str(ROOT / "scripts/ros_env.sh")],
        env=env, capture_output=True, text=True, check=True,
    )

    assert result.stdout.strip() == expected


def test_cyclone_runtime_dependency_is_declared():
    package = ET.parse(ROOT / "src/robot_description/package.xml").getroot()
    assert "rmw_cyclonedds_cpp" in {dep.text for dep in package.findall("exec_depend")}


@pytest.mark.parametrize("selection, message", [
    ("", "Select the project RMW first"),
    ("rmw_fastrtps_cpp", "differs from loaded"),
])
def test_smoke_rejects_missing_or_mismatched_rmw(selection, message):
    code = """
import os, sys
sys.path.insert(0, sys.argv[1])
import rclpy
import test_gazebo_smoke as smoke
rclpy.init()
try:
    os.environ['RMW_IMPLEMENTATION'] = sys.argv[2]
    try:
        with smoke.ros_observer(1, {'environment': {}}):
            pass
    except AssertionError as error:
        assert sys.argv[3] in str(error), str(error)
    else:
        raise AssertionError('Observer accepted missing or mismatched middleware')
finally:
    rclpy.try_shutdown()
"""
    env = dict(os.environ, RMW_IMPLEMENTATION="rmw_cyclonedds_cpp")
    subprocess.run(
        [sys.executable, "-B", "-c", code, str(Path(__file__).parent),
         selection, message], env=env, capture_output=True, text=True, check=True,
    )
