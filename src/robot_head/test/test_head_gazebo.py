"""Physical joint acceptance in the installed head-control launch."""
import math
import time
import pytest
from ament_index_python.packages import get_package_share_directory
from pathlib import Path
from rclpy.time import Time
from conftest import head_simulation, restart_on_reset, write_report, restarting_test
from robot_head.model import load_limits


def assert_limits(probe):
    model = Path(get_package_share_directory("robot_description")) / "urdf/robot.urdf"
    limits = load_limits(model)
    assert probe.trace, "No measured joint samples"
    from conftest import verify_feedback
    probe.finish_feedback()
    verify_feedback(probe.actual_trace, probe.trace, probe.raw_source_times)
    for stamp, position, velocity in probe.trace:
        assert math.isfinite(position) and limits.lower <= position <= limits.upper, (stamp, position)
        assert velocity is not None and math.isfinite(velocity), "Missing actual joint velocity"
        assert abs(velocity) <= limits.velocity, (stamp, velocity)


def aiming(probe, deadline, report, initial, target):
    probe.ready(min(deadline, time.monotonic()+60))
    report["targets"] = []
    if initial is not None:
        report["targets"].append(probe.hold(math.radians(initial), deadline))
    report["targets"].append(probe.hold(math.radians(target), deadline))
    for frame in ("base_link", "head_link", "left_track_link", "right_track_link"):
        assert probe.buffer.can_transform("base_footprint", frame, Time()), frame
    assert_limits(probe)
    report["position_velocity_limits"] = "PASS"
    report["body_relative_joint_motion"] = "PASS"
    from conftest import verify_feedback
    report["max_public_measured_error_rad"] = verify_feedback(probe.actual_trace, probe.trace, probe.raw_source_times)
    report["public_measured_pairs"] = len(probe.actual_trace)


@pytest.mark.parametrize("initial,target", [(None,0), (0,15), (0,-15), (15,-15), (-15,15), (15,0), (-15,0)])
def test_head_targets_hold_and_feedback(tmp_path, initial, target):
    report, error = {}, None
    deadline = time.monotonic() + 60 * 3
    try:
        restart_on_reset(lambda: head_simulation(tmp_path, report),
            lambda probe, deadline: aiming(probe, deadline, report, initial, target), deadline,
            report.setdefault("attempts", []))
    except BaseException as caught:
        error = caught
        raise
    finally:
        write_report(tmp_path, report, error)


@pytest.mark.parametrize("reset_phase", ["travel", "hold"])
def test_clock_reset_restarts_only_current_test(tmp_path, reset_phase):
    report, error = {}, None
    injected = False
    def scenario(probe, deadline):
        nonlocal injected
        probe.ready(min(deadline, time.monotonic()+60))
        def hook(probe, stamp, actual, window):
            nonlocal injected
            during_travel = math.radians(2) < abs(actual) < math.radians(12)
            partial_hold = window.start is not None and stamp-window.start >= 1_000_000_000
            if not injected and ((reset_phase == "travel" and during_travel) or
                                 (reset_phase == "hold" and partial_hold)):
                injected = True
                report["reset_injected"] = {"phase": reset_phase, "stamp_ns": stamp}
                probe.reset_world()
        result = probe.hold(math.pi/12, deadline, hook)
        report["accepted_hold"] = result
        assert injected
        assert_limits(probe)
    try:
        restart_on_reset(lambda: head_simulation(tmp_path, report), scenario,
                         time.monotonic()+60*3, report.setdefault("attempts", []))
        statuses = [a["status"] for a in report["attempts"]]
        assert statuses[-1] == "PASS" and len(statuses) >= 2
        assert all(status == "INVALIDATED" for status in statuses[:-1])
        assert len(report["launches"]) == len(statuses)
    except BaseException as caught:
        error = caught
        raise
    finally:
        write_report(tmp_path, report, error)


@pytest.mark.parametrize("boundary", [-0.610865,0.610865])
def test_boundaries_invalid_recovery(tmp_path, boundary):
    report, error = {}, None
    def scenario(probe, deadline):
        probe.ready(min(deadline, time.monotonic()+60))
        limits = load_limits(Path(get_package_share_directory("robot_description")) / "urdf/robot.urdf")
        results = [probe.hold(boundary, deadline)]
        for invalid in (math.nextafter(limits.upper, math.inf),
                        math.nextafter(limits.lower, -math.inf), float("nan"),
                        float("inf"), -float("inf")):
            count = len(probe.accepted)
            start = probe.sim_ns
            probe.publish(invalid)
            probe.wait_for(lambda: probe.sim_ns - start >= 200_000_000, min(deadline, time.monotonic()+60))
            assert len(probe.accepted) == count, "Invalid target was accepted"
            assert abs(probe.actual[-1] - results[-1]["target_rad"]) <= math.pi/90
        results.append(probe.hold(0, deadline))
        report["targets"] = results
        report["invalid_inputs_rejected"] = 5
        assert_limits(probe)
    try:
        restart_on_reset(lambda: head_simulation(tmp_path, report), scenario,
                         time.monotonic()+60*5, report.setdefault("attempts", []))
    except BaseException as caught:
        error = caught
        raise
    finally:
        write_report(tmp_path, report, error)


@restarting_test(phases=2)
def test_disabled_actuator_cannot_pass_nonzero_target(tmp_path):
    report, error = {}, None
    model = Path(get_package_share_directory("robot_description")) / "urdf/robot.urdf"
    try:
        with head_simulation(tmp_path, report, [f"model_file:={model}"]) as probe:
            probe.ready(time.monotonic()+60)
            with pytest.raises(AssertionError, match="deadline"):
                probe.hold(math.pi/12, time.monotonic()+5)
            assert probe.accepted[-1] == math.pi/12
            assert abs(probe.last_sample[1]) < math.radians(2)
        report["negative_proof"] = "Nonzero target failed despite accepted command and active feedback"
    except BaseException as caught:
        error = caught
        raise
    finally:
        write_report(tmp_path, report, error)


@restarting_test(phases=2)
def test_missing_joint_feedback_cannot_pass(tmp_path):
    report = {}
    with head_simulation(tmp_path, report) as probe:
        probe.ready(time.monotonic()+60)
        probe.node.destroy_subscription(probe.raw_sub)
        with pytest.raises(AssertionError, match="deadline"):
            probe.hold(math.pi/12, time.monotonic()+2)
    report["negative_proof"] = "Accepted target and actual topic cannot replace missing raw observation"
    write_report(tmp_path, report)


@restarting_test(phases=2)
def test_interruption_and_early_exit_cleanup(tmp_path):
    import os
    import signal
    from conftest import live_members
    report = {}
    with pytest.raises(KeyboardInterrupt):
        with head_simulation(tmp_path, report) as probe:
            probe.ready(time.monotonic()+60)
            group = probe.process.pid
            os.kill(os.getpid(), signal.SIGTERM)
    assert not live_members(group)
    with head_simulation(tmp_path, report) as probe:
        probe.ready(time.monotonic()+60)
        group = probe.process.pid
        os.killpg(group, signal.SIGINT)
        probe.process.wait(timeout=10)
        with pytest.raises(AssertionError, match="exited unexpectedly"):
            probe.poll(time.monotonic()+10)
    assert not live_members(group)
    report["interruption_cleanup"] = "PASS"
    report["early_exit_detection"] = "PASS"
    write_report(tmp_path, report)


@restarting_test(phases=2)
def test_feedback_interruption_recovery_requires_new_full_hold(tmp_path):
    report, injected = {}, False
    with head_simulation(tmp_path, report) as probe:
        probe.ready(time.monotonic()+60)
        def interrupt(probe, stamp, actual, window):
            nonlocal injected
            if not injected and window.start is not None and stamp-window.start >= 1_000_000_000:
                injected = True
                probe.suspend_until = stamp + 1_000_000_000
                report["recovery_not_before_ns"] = probe.suspend_until
        report["hold"] = probe.hold(math.pi/12, time.monotonic()+60, interrupt)
        assert injected
        assert report["hold"]["hold_start_ns"] >= report["recovery_not_before_ns"]
        assert report["hold"]["hold_seconds"] >= 3
        assert_limits(probe)
    write_report(tmp_path, report)


@restarting_test(phases=2)
def test_corrupted_target_echo_actual_is_detected(tmp_path):
    from std_msgs.msg import Float64
    from conftest import verify_feedback
    report = {}
    with head_simulation(tmp_path, report) as probe:
        probe.ready(time.monotonic()+60)
        corrupted = probe.node.create_publisher(Float64, "/head/pitch/actual", 10)
        probe.wait_for(lambda: corrupted.get_subscription_count() > 0, time.monotonic()+10)
        corrupted.publish(Float64(data=math.pi/12))
        probe.wait_for(lambda: any(r["actual"] == math.pi/12 for r in probe.actual_trace), time.monotonic()+10)
        probe.finish_feedback()
        genuine = [r for r in probe.actual_trace if r["actual"] != math.pi/12]
        verify_feedback(genuine, probe.trace, probe.raw_source_times)
        with pytest.raises(AssertionError, match="measured"):
            verify_feedback(probe.actual_trace, probe.trace, probe.raw_source_times)
    report["target_echo_rejected_against_raw_state"] = "PASS"
    write_report(tmp_path, report)


@restarting_test(phases=3)
def test_publisher_loss_and_adapter_shutdown(tmp_path):
    report = {}
    with head_simulation(tmp_path, report) as probe:
        deadline = time.monotonic() + 60 * 3
        probe.ready(min(deadline, time.monotonic()+60))
        results = []
        results.append(probe.hold(math.pi/12, deadline))
        probe.node.destroy_publisher(probe.target)
        start = probe.sim_ns
        probe.wait_for(lambda: probe.sim_ns-start >= 3_000_000_000, min(deadline, time.monotonic()+60))
        assert abs(probe.actual[-1]-math.pi/12) <= math.pi/90
        report["publisher_loss_retains_target"] = "PASS"
        import os, signal
        from conftest import live_members
        adapter = [pid for pid in live_members(probe.process.pid)
                   if any(part.endswith(b"/head_pitch_node") for part in
                          Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0"))]
        assert len(adapter) == 1, adapter
        os.kill(adapter[0], signal.SIGINT)
        probe.wait_for(lambda: probe.node.count_publishers("/head_pitch_joint/reference") == 0,
                       min(deadline, time.monotonic()+60))
        count, start = len(probe.reference), probe.sim_ns
        probe.wait_for(lambda: probe.sim_ns-start >= 3_000_000_000, min(deadline, time.monotonic()+60))
        assert len(probe.reference) == count, "Adapter emitted a command after shutdown"
        report["adapter_shutdown"] = "PASS"
        assert_limits(probe)
        report["targets"] = results
    write_report(tmp_path, report)
