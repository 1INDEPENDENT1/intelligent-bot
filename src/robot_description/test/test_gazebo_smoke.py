"""Observe the real installed launch; no GUI, controller, or hardware required."""
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
import uuid

from domain_coordinator import domain_id
import rclpy
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from rclpy.utilities import get_rmw_implementation_identifier
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import JointState
from tf2_ros import Buffer, TransformException, TransformListener


OBSERVATION_SECONDS = 60
CLEANUP_SECONDS = 10
FRAMES = ("base_link", "left_track_link", "right_track_link", "head_link")


def record(report, name, status, **evidence):
    report["checks"][name] = {"status": status, "evidence": evidence}


def check_cancelled():
    marker = os.environ.get("ROBOT_DESCRIPTION_TEST_CANCEL_FILE")
    assert not (marker and Path(marker).exists()), "Check command interrupted"


def signal_group(pgid, signum):
    try:
        os.killpg(pgid, signum)
    except ProcessLookupError:
        pass  # The last process may have exited since live_group().


def live_group(pgid):
    """Count only live members of our process group (ignore unreaped zombies)."""
    members = []
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == pgid and fields[0] != "Z":
                members.append(int(path.parent.name))
        except (FileNotFoundError, ProcessLookupError):
            pass
    return members


@contextmanager
def launched_robot(env, log_path, report):
    """Own and clean up only the launch process group, including on SIGTERM."""
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"Smoke test interrupted by signal {signum}")

    previous = signal.signal(signal.SIGTERM, interrupted)
    previous_int = signal.getsignal(signal.SIGINT)
    process = None
    try:
        with log_path.open("w") as output:
            check_cancelled()
            process = subprocess.Popen(
                ["ros2", "launch", "robot_description", "gazebo.launch.py", "gui:=false"],
                env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
            )
            print(f"Test-owned launch process group: {process.pid}", flush=True)
            try:
                yield process
            finally:
                # A repeated interruption must not interrupt owned-process cleanup.
                previous_int = signal.signal(signal.SIGINT, signal.SIG_IGN)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                if live_group(process.pid):
                    signal_group(process.pid, signal.SIGINT)
                deadline = time.monotonic() + CLEANUP_SECONDS
                while live_group(process.pid) and time.monotonic() < deadline:
                    process.poll()
                    time.sleep(0.1)
                if live_group(process.pid):
                    signal_group(process.pid, signal.SIGKILL)
                process.wait(timeout=CLEANUP_SECONDS)
                # Allow the kernel to finish reaping descendants after a forced stop.
                deadline = time.monotonic() + CLEANUP_SECONDS
                while live_group(process.pid) and time.monotonic() < deadline:
                    time.sleep(0.1)
                remaining = live_group(process.pid)
                record(report, "cleanup", "FAIL" if remaining else "PASS",
                       process_group=process.pid, remaining_processes=remaining)
                assert not remaining, "Test-owned processes survived cleanup"
                print(f"Cleaned launch process group: {process.pid}", flush=True)
    finally:
        if process is not None:
            signal.signal(signal.SIGINT, previous_int)
        signal.signal(signal.SIGTERM, previous)
        if log_path.exists():
            print(log_path.read_text(errors="replace"))


@contextmanager
def ros_observer(reserved_domain, report):
    """Keep ROS setup and teardown outside the observation behavior."""
    selected_rmw = os.environ.get("RMW_IMPLEMENTATION")
    assert selected_rmw, "Select the project RMW first: source scripts/ros_env.sh"
    report["environment"]["selected_middleware"] = selected_rmw
    context = Context()
    context.init(domain_id=reserved_domain)
    node = executor = listener = None
    try:
        actual_rmw = get_rmw_implementation_identifier()
        report["environment"]["observer_middleware"] = actual_rmw
        assert actual_rmw == selected_rmw, (
            f"Selected middleware {selected_rmw} differs from loaded {actual_rmw}"
        )
        node = rclpy.create_node("baseline_observer", context=context)
        executor = SingleThreadedExecutor(context=context)
        executor.add_node(node)
        buffer = Buffer()
        listener = TransformListener(buffer, node)
        samples = {"clock_count": 0, "clock_values": [], "joint_count": 0,
                   "joint_names": [], "head_position": None, "joint_valid": False}

        def on_clock(message):
            samples["clock_count"] += 1
            value = message.clock.sec * 1_000_000_000 + message.clock.nanosec
            values = samples["clock_values"]
            if not values or value > values[-1]:
                values.append(value)
                del values[:-2]

        def on_joints(message):
            samples["joint_count"] += 1
            samples["joint_names"] = list(message.name)
            samples["head_position"] = None
            if "head_pitch_joint" in message.name:
                index = message.name.index("head_pitch_joint")
                if index < len(message.position):
                    samples["head_position"] = message.position[index]
            value = samples["head_position"]
            samples["joint_valid"] = value is not None and math.isfinite(value)

        node.create_subscription(Clock, "/clock", on_clock, qos_profile_sensor_data)
        node.create_subscription(JointState, "/joint_states", on_joints, qos_profile_sensor_data)
        report["environment"]["observer_domain"] = context.get_domain_id()
        yield node, executor, buffer, samples
    finally:
        if listener is not None:
            listener.unregister()
        if executor is not None:
            executor.shutdown()
        if node is not None:
            node.destroy_node()
        context.shutdown()


def collect_ros(buffer, samples, report):
    """Distinguish absent messages from received data that violates a condition."""
    record(report, "clock", "PASS" if len(samples["clock_values"]) >= 2 else
           "FAIL" if samples["clock_count"] else "NOT OBSERVED",
           messages=samples["clock_count"], increasing_timestamps_ns=samples["clock_values"][:])
    record(report, "joint_state", "PASS" if samples["joint_valid"] else
           "FAIL" if samples["joint_count"] else "NOT OBSERVED",
           messages=samples["joint_count"], last_names=samples["joint_names"],
           last_head_position=repr(samples["head_position"]))
    for frame in FRAMES:
        name = f"TF base_footprint -> {frame}"
        if not buffer.can_transform("base_footprint", frame, Time()):
            record(report, name, "NOT OBSERVED", reason="Transform unavailable")
            continue
        try:
            transform = buffer.lookup_transform("base_footprint", frame, Time())
            t, r = transform.transform.translation, transform.transform.rotation
            values = [t.x, t.y, t.z, r.x, r.y, r.z, r.w]
            finite = all(math.isfinite(value) for value in values)
            record(report, name, "PASS" if finite else "FAIL",
                   translation_and_quaternion=[repr(value) for value in values])
        except TransformException as error:
            record(report, name, "FAIL", error=str(error))


@contextmanager
def gazebo_observer(env, report):
    """Sample model listings asynchronously; never wait for Gazebo in the ROS loop."""
    process = None
    attempts = 0
    next_sample = 0.0
    unavailable = False
    # File-backed output cannot fill a pipe and block the query subprocess.
    with tempfile.TemporaryFile(mode="w+") as output:
        def poll(allow_start=True):
            nonlocal process, attempts, next_sample, unavailable
            if unavailable:
                return
            if process is not None:
                if process.poll() is None:
                    return
                output.seek(0)
                listing = output.read()
                code = process.returncode
                for name, found in (
                    ("gazebo_world", "minimal" in listing),
                    ("gazebo_model", bool(re.search(r"(?m)^\s*-\s+my_robot\s*$", listing))),
                ):
                    record(report, name, "PASS" if code == 0 and found else "FAIL",
                           command="gz model --list", exit_code=code, output=listing,
                           completed_samples=attempts)
                process = None
                next_sample = time.monotonic() + 1.0
            if all(report["checks"][name]["status"] == "PASS"
                   for name in ("gazebo_world", "gazebo_model")):
                return
            if allow_start and time.monotonic() >= next_sample:
                output.seek(0)
                output.truncate()
                try:
                    process = subprocess.Popen(
                        ["gz", "model", "--list"], env=env, stdout=output,
                        stderr=subprocess.STDOUT, start_new_session=True,
                    )
                    attempts += 1
                except OSError as error:
                    unavailable = True
                    for name in ("gazebo_world", "gazebo_model"):
                        record(report, name, "FAIL", error=str(error))

        try:
            yield poll
        finally:
            # Preserve partial query output as evidence, then stop only its group.
            if process is not None:
                signal_group(process.pid, signal.SIGKILL)
                process.wait(timeout=CLEANUP_SECONDS)
                output.seek(0)
                report["gazebo_pending_query_output"] = output.read()
                for name in ("gazebo_world", "gazebo_model"):
                    if report["checks"][name]["status"] == "NOT OBSERVED":
                        record(report, name, "NOT OBSERVED",
                               reason="No completed model listing within observation period",
                               query_pid=process.pid)
            report["gazebo_queries_started"] = attempts
            report["gazebo_query_pending_at_stop"] = process is not None


def graph_snapshot(node, report):
    """Supplement assertions with discovery evidence, without inferring a root cause."""
    try:
        report["ros_graph"] = {
            "nodes": node.get_node_names(),
            "publishers": {
                topic: [{"node": info.node_name, "namespace": info.node_namespace,
                         "type": info.topic_type, "qos": str(info.qos_profile)}
                        for info in node.get_publishers_info_by_topic(topic)]
                for topic in ("/clock", "/joint_states", "/tf", "/tf_static")
            },
        }
    except Exception as error:
        report["ros_graph"] = {"snapshot_error": str(error)}


def observe(ros, process, env, report):
    node, executor, buffer, samples = ros
    started = time.monotonic()
    deadline = started + OBSERVATION_SECONDS
    required = [name for name in report["checks"] if name != "cleanup"]
    try:
        with gazebo_observer(env, report) as poll_gazebo:
            while time.monotonic() < deadline:
                check_cancelled()
                code = process.poll()
                record(report, "launch", "PASS" if code is None else "FAIL",
                       pid=process.pid, exit_code=code)
                poll_gazebo()
                executor.spin_once(timeout_sec=min(0.1, max(0, deadline - time.monotonic())))
                collect_ros(buffer, samples, report)
                if code is not None:
                    report["observation_end"] = "Launch exited early"
                    break
                if all(report["checks"][name]["status"] == "PASS" for name in required):
                    report["observation_end"] = "All required observations obtained"
                    break
            else:
                report["observation_end"] = "Observation deadline reached"
            poll_gazebo(allow_start=False)
            code = process.poll()
            record(report, "launch", "PASS" if code is None else "FAIL",
                   pid=process.pid, exit_code=code)
    finally:
        report["observation_seconds"] = round(time.monotonic() - started, 3)
        graph_snapshot(node, report)


@contextmanager
def isolated_environment(tmp_path, monkeypatch, report):
    with domain_id() as reserved_domain:
        monkeypatch.setenv("ROS_DOMAIN_ID", str(reserved_domain))
        env = dict(os.environ, ROS_DOMAIN_ID=str(reserved_domain),
                   GZ_PARTITION=f"robot-description-test-{uuid.uuid4().hex}",
                   ROS_LOG_DIR=str(tmp_path / "ros-logs"))
        settings = ("ROS_DOMAIN_ID", "GZ_PARTITION", "RMW_IMPLEMENTATION",
                    "ROS_AUTOMATIC_DISCOVERY_RANGE", "ROS_LOCALHOST_ONLY",
                    "ROS_STATIC_PEERS", "ROS_DISCOVERY_SERVER",
                    "FASTRTPS_DEFAULT_PROFILES_FILE", "FASTDDS_DEFAULT_PROFILES_FILE")
        report["environment"]["launch_settings"] = {
            key: env.get(key, "<unset>") for key in settings}
        yield reserved_domain, env


def test_headless_gazebo_baseline(tmp_path, monkeypatch):
    """Missing spawn, clock, joint state, TF, or failed cleanup must fail the test."""
    names = ["launch", "gazebo_world", "gazebo_model", "clock", "joint_state",
             *(f"TF base_footprint -> {frame}" for frame in FRAMES), "cleanup"]
    report = {"checks": {name: {"status": "NOT OBSERVED", "evidence": {}}
                         for name in names}, "environment": {}}
    try:
        check_cancelled()
        with isolated_environment(tmp_path, monkeypatch, report) as (reserved_domain, env):
            with ros_observer(reserved_domain, report) as ros:
                with launched_robot(env, tmp_path / "launch.log", report) as process:
                    observe(ros, process, env, report)
    except BaseException as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["result"] = "PASS" if "error" not in report and all(
            check["status"] == "PASS" for check in report["checks"].values()) else "FAIL"
        print("\nSMOKE TEST REPORT\n" + json.dumps(report, indent=2), flush=True)
    unmet = [name for name, check in report["checks"].items() if check["status"] != "PASS"]
    assert not unmet, "Required checks not PASS: " + ", ".join(unmet)
