"""Head limits, target policy and generated actuator contracts."""
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
import yaml
from robot_head.model import load_limits
from robot_head.policy import HeadPolicy, measured_pitch
from robot_head.simulation_model import generate_model

from ament_index_python.packages import get_package_share_directory
URDF = Path(get_package_share_directory("robot_description")) / "urdf/robot.urdf"

@pytest.fixture
def limits():
    return load_limits(URDF)

def test_limits_and_sign(limits):
    policy = HeadPolicy(limits)
    assert limits.lower == -0.610865
    assert limits.upper == 0.610865
    assert limits.velocity == 1.0
    assert limits.effort == 0.1765
    assert policy.accept(math.pi / 12)
    assert policy.target == pytest.approx(-math.pi / 12)
    assert measured_pitch(["head_pitch_joint"], [0.2]) == -0.2

@pytest.mark.parametrize("target", [float("nan"), float("inf"), -float("inf"),
    math.nextafter(0.610865, math.inf), math.nextafter(-0.610865, -math.inf)])
def test_invalid_target_retains_state(limits, target):
    policy = HeadPolicy(limits)
    policy.accept(0.2)
    policy.advance(1_000_000_000)
    policy.advance(1_100_000_000)
    before = (policy.target, policy.reference)
    assert not policy.accept(target)
    assert (policy.target, policy.reference) == before

@pytest.mark.parametrize("target", [-0.610865, 0.610865, 0.0])
def test_boundaries_are_inclusive(limits, target):
    assert HeadPolicy(limits).accept(target)

def test_reference_slew_duplicate_and_rewind(limits):
    policy = HeadPolicy(limits)
    policy.accept(-0.5)
    assert policy.advance(1_000_000_000) == 0
    assert policy.advance(1_100_000_000) == pytest.approx(0.1)
    assert policy.advance(1_100_000_000) == pytest.approx(0.1)
    assert policy.advance(0) == pytest.approx(0.1)
    assert policy.target == 0.5
    assert policy.advance(100_000_000) == pytest.approx(0.2)
    policy.accept(0)
    assert policy.advance(200_000_000) == pytest.approx(0.1)

@pytest.mark.parametrize("names,positions", [([], []), (["other"], [0.1]),
    (["head_pitch_joint"], []), (["head_pitch_joint"], [float("nan")])])
def test_bad_measurement_has_no_actual(names, positions):
    assert measured_pitch(names, positions) is None

@pytest.mark.parametrize("field,value", [("lower", "nan"), ("upper", "-1"),
    ("velocity", "0"), ("effort", "inf")])
def test_invalid_model_is_not_given_fallback_limits(tmp_path, field, value):
    tree = ET.parse(URDF)
    tree.find(".//joint[@name='head_pitch_joint']/limit").set(field, value)
    path = tmp_path / "bad.urdf"
    tree.write(path)
    with pytest.raises(ValueError):
        load_limits(path)

def test_missing_joint_is_configuration_error(tmp_path):
    path = tmp_path / "empty.urdf"
    path.write_text("<robot name='empty'/>")
    with pytest.raises(ValueError):
        load_limits(path)

def test_generated_model_preserves_joint_and_limits(tmp_path, limits):
    path = tmp_path / "head.urdf"
    generate_model(URDF, path, {"p_gain": 0.05, "i_gain": 0.0, "d_gain": 0.006})
    original = ET.parse(URDF).find("joint[@name='head_pitch_joint']")
    generated = ET.parse(path)
    assert ET.tostring(generated.find("joint[@name='head_pitch_joint']")) == ET.tostring(original)
    plugin = generated.find(".//plugin[@name='gz::sim::systems::JointPositionController']")
    assert plugin.findtext("use_velocity_commands") == "false"
    assert float(plugin.findtext("cmd_max")) == limits.effort
    assert float(plugin.findtext("cmd_min")) == -limits.effort
    assert plugin.findtext("initial_position") == "0"
    assert generated.find(".//plugin[@name='gz::sim::systems::JointStatePublisher']") is not None

@pytest.mark.parametrize("config", [{}, {"effort": 1.0}, {"p_gain": float("nan")},
    {"p_gain": -1}, {"use_velocity_commands": True}])
def test_configuration_cannot_bypass_model_limits(tmp_path, config):
    with pytest.raises(ValueError):
        generate_model(URDF, tmp_path / "head.urdf", config)


def test_hold_requires_three_continuous_simulation_seconds():
    from conftest import HoldWindow
    hold = HoldWindow(0.2, sample_period_ns=1_000_000_000)
    for stamp in (0, 1_000_000_000, 2_000_000_000, 2_999_999_999):
        assert not hold.observe(stamp, 0.2)
    assert hold.observe(3_000_000_000, 0.2)


@pytest.mark.parametrize("bad", [float("nan"), 0.3])
def test_duplicate_invalid_sample_clears_hold(bad):
    from conftest import HoldWindow
    hold = HoldWindow(0.2, sample_period_ns=1_000_000_000)
    for stamp in (0, 1_000_000_000, 2_000_000_000):
        assert not hold.observe(stamp, 0.2)
    assert not hold.observe(2_000_000_000, bad)
    assert not hold.observe(3_000_000_000, 0.2)
    for stamp in (4_000_000_000, 5_000_000_000):
        assert not hold.observe(stamp, 0.2)
    assert hold.observe(6_000_000_000, 0.2)


def test_missing_stream_restarts_hold_on_recovery():
    from conftest import HoldWindow
    hold = HoldWindow(0, sample_period_ns=1_000_000_000)
    assert not hold.observe(0, 0)
    assert not hold.observe(1_000_000_000, 0)
    assert not hold.observe(3_000_000_000, 0)
    assert not hold.observe(4_000_000_000, 0)
    assert not hold.observe(5_000_000_000, 0)
    assert hold.observe(6_000_000_000, 0)


def test_duplicate_and_rewound_measurements_cannot_pass():
    from conftest import HoldWindow, ClockReset
    hold = HoldWindow(0, sample_period_ns=1_000_000_000)
    assert not hold.observe(2_000_000_000, 0)
    assert not hold.observe(2_000_000_000, 0)
    with pytest.raises(ClockReset):
        hold.observe(0, 0)


def test_restarting_discards_attempt_and_does_not_extend_budget():
    from conftest import restart_on_reset, ClockReset
    from contextlib import contextmanager
    import time
    attempts, closed = [], []
    deadline = time.monotonic() + 5
    @contextmanager
    def setup():
        attempts.append(len(attempts) + 1)
        try:
            yield attempts[-1]
        finally:
            closed.append(attempts[-1])
    def scenario(number, original_deadline):
        assert original_deadline == deadline
        if number == 1:
            raise ClockReset("injected")
        return number
    outcomes = []
    assert restart_on_reset(setup, scenario, deadline, outcomes) == 2
    assert closed == [1, 2]
    assert outcomes[0]["status"] == "INVALIDATED"
    with pytest.raises(AssertionError, match="budget"):
        restart_on_reset(setup, scenario, time.monotonic() - 1, [])


@pytest.mark.parametrize("target,actual", [(math.pi/12, -math.pi/12),
    (math.pi/12, 0.0), (0.0, math.radians(2.01))])
def test_wrong_direction_locked_joint_and_excess_error_cannot_pass(target, actual):
    from conftest import HoldWindow
    window = HoldWindow(target, sample_period_ns=1_000_000_000)
    control = HoldWindow(target, sample_period_ns=1_000_000_000)
    stamps = [0, 1_000_000_000, 2_000_000_000, 3_000_000_000]
    assert [window.observe(stamp, actual) for stamp in stamps] == [False]*4
    assert [control.observe(stamp, target) for stamp in stamps] == [False, False, False, True]


def test_repeated_resets_exhaust_original_budget():
    from conftest import restart_on_reset, ClockReset
    from contextlib import contextmanager
    from unittest.mock import patch
    @contextmanager
    def setup():
        yield object()
    def reset(observation, deadline):
        raise ClockReset("injected repeatedly")
    outcomes = []
    with patch("conftest.time.monotonic", side_effect=[0, 1, 3]):
        with pytest.raises(AssertionError, match="budget"):
            restart_on_reset(setup, reset, 2, outcomes)
    assert [o["status"] for o in outcomes] == ["INVALIDATED", "INVALIDATED"]


def test_public_feedback_echo_is_rejected_against_measurement():
    from conftest import verify_feedback
    records = [{"actual": math.pi/12, "dds_source_ns": 20}]
    raw = [(0, 0.0, 0.0)]
    with pytest.raises(AssertionError, match="measured"):
        verify_feedback(records, raw, [10])


def test_feedback_pairing_handles_observer_queue_skew_without_future_credit():
    from conftest import verify_feedback
    raw = [(i, -i/10, 0.0) for i in range(4)]
    records = [{"actual": 0.1, "dds_source_ns": 25, "raw_receipt_index": 0},
               {"actual": 0.3, "dds_source_ns": 45, "raw_receipt_index": 0}]
    assert verify_feedback(records, raw, [10, 20, 30, 40]) == 0
    assert [r["measured_index"] for r in records] == [1, 3]
    with pytest.raises(AssertionError, match="measured"):
        verify_feedback([{"actual": 0.3, "dds_source_ns": 25}], raw, [10, 20, 30, 40])


def test_source_metadata_supports_jazzy_callback_dictionary():
    from conftest import source_time
    from types import SimpleNamespace
    assert source_time({"source_timestamp": 123}) == 123
    assert source_time(SimpleNamespace(source_timestamp=456)) == 456


@pytest.mark.parametrize("raw_times,actual_times", [([10, 5], [20, 30]),
                                                   ([10, 20], [30, 25])])
def test_source_clock_rewind_invalidates_association(raw_times, actual_times):
    from conftest import verify_feedback, ClockReset
    raw = [(0, -0.1, 0.0), (1, -0.2, 0.0)]
    records = [{"actual": value, "dds_source_ns": stamp}
               for value, stamp in zip((0.1, 0.2), actual_times)]
    with pytest.raises(ClockReset):
        verify_feedback(records, raw, raw_times)


def test_feedback_audit_drains_source_before_comparison():
    from conftest import GazeboProbe
    from types import SimpleNamespace
    destroyed = []
    raw_times = [10]
    def wait_for(predicate, deadline):
        assert not predicate()
        raw_times.append(30)
        assert predicate()
    probe = SimpleNamespace(actual_sub="subscription", node=SimpleNamespace(
        destroy_subscription=lambda sub: destroyed.append(sub)),
        actual_trace=[{"dds_source_ns": 25}], raw_source_times=raw_times,
        observation_deadline=100, wait_for=wait_for)
    GazeboProbe.finish_feedback(probe)
    assert destroyed == ["subscription"]
    assert probe.actual_sub is None


@pytest.mark.parametrize("direction", [-1, 1])
def test_configured_motion_takes_one_and_half_seconds_per_fifteen_degrees(limits, direction):
    share = Path(get_package_share_directory("robot_head"))
    config = yaml.safe_load((share / "config/head_control.yaml").read_text())
    policy = HeadPolicy(limits, config["reference_speed_scale"])
    assert policy.speed == pytest.approx(math.radians(10))

    assert policy.accept(direction * math.radians(15))
    assert policy.advance(0) == 0
    assert policy.advance(1_000_000_000) == pytest.approx(-direction * math.radians(10))
    assert policy.advance(1_500_000_000) == pytest.approx(-direction * math.radians(15))
    assert policy.advance(2_000_000_000) == pytest.approx(-direction * math.radians(15))

    assert policy.accept(-direction * math.radians(15))
    assert policy.advance(3_000_000_000) == pytest.approx(-direction * math.radians(5))
    assert policy.advance(5_000_000_000) == pytest.approx(direction * math.radians(15))
