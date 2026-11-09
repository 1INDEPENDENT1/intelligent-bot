"""Fast checks of the installed description's documented public contract."""
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import pytest


@pytest.fixture
def share():
    return Path(get_package_share_directory("robot_description"))


def test_installed_resources(share):
    """Catch missing install entries and broken mesh URIs."""
    for relative in (
        "urdf/robot.urdf", "launch/gazebo.launch.py",
        "worlds/minimal.sdf", "config/bridge.yaml",
    ):
        assert (share / relative).is_file(), f"Missing installed resource: {relative}"

    robot = ET.parse(share / "urdf/robot.urdf").getroot()
    for mesh in robot.findall(".//mesh"):
        uri = mesh.attrib["filename"]
        assert uri.startswith("package://"), f"Expected package mesh URI: {uri}"
        package, relative = uri[len("package://"):].split("/", 1)
        mesh_path = Path(get_package_share_directory(package)) / relative
        assert mesh_path.is_file(), f"Missing installed mesh: {uri}"


def test_model_contract(share):
    """Catch accidental frame/joint interface changes and invalid head limits."""
    robot = ET.parse(share / "urdf/robot.urdf").getroot()
    links = {link.attrib["name"] for link in robot.findall("link")}
    expected_links = {
        "base_footprint", "base_link", "head_link",
        "left_track_link", "right_track_link",
    }
    assert expected_links <= links, f"Missing public frames: {expected_links - links}"
    joints = {joint.attrib["name"]: joint for joint in robot.findall("joint")}
    for name, parent, child, kind in (
        ("base_footprint_joint", "base_footprint", "base_link", "fixed"),
        ("head_pitch_joint", "base_link", "head_link", "revolute"),
        ("left_track_joint", "base_link", "left_track_link", "fixed"),
        ("right_track_joint", "base_link", "right_track_link", "fixed"),
    ):
        assert name in joints, f"Missing public joint: {name}"
        joint = joints[name]
        actual = (joint.find("parent").get("link"),
                  joint.find("child").get("link"), joint.get("type"))
        assert actual == (parent, child, kind), f"Joint contract changed: {name}: {actual}"

    head = joints["head_pitch_joint"]
    axis = [float(value) for value in head.find("axis").get("xyz").split()]
    assert axis == [0.0, 1.0, 0.0], f"Head pitch must use the Y axis: {axis}"
    limits = head.find("limit")
    assert limits is not None, "Missing head joint limits"
    lower, upper, effort, velocity = (
        float(limits.attrib[key]) for key in ("lower", "upper", "effort", "velocity")
    )
    assert all(math.isfinite(v) for v in (lower, upper, effort, velocity)), "Non-finite head limits"
    assert lower < upper, "Head lower limit must be less than upper limit"
    assert effort > 0 and velocity > 0, "Head effort and velocity must be positive"
