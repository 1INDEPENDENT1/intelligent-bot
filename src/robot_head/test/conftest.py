"""Test import setup; process/observation fixtures added with system tests."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import math
import time

class ClockReset(RuntimeError):
    """Only this condition permits restarting the affected test."""

class HoldWindow:
    def __init__(self, target, sample_period_ns):
        assert sample_period_ns > 0
        self.target = target
        self.sample_period_ns = sample_period_ns
        self.start = None
        self.previous = None
        self.samples = 0
        self.errors = []

    def observe(self, stamp_ns, actual):
        if self.previous is not None and stamp_ns < self.previous:
            raise ClockReset("Joint-state timestamp rewound")
        error = abs(actual - self.target)
        if not math.isfinite(actual) or error > math.pi / 90:
            self.start = None
            self.previous = stamp_ns
            return False
        if stamp_ns == self.previous:
            return False
        if self.previous is not None and stamp_ns-self.previous > self.sample_period_ns:
            self.start = None
        self.previous = stamp_ns
        self.errors.append(error)
        self.samples += 1
        if self.start is None:
            self.start = stamp_ns
        return stamp_ns - self.start >= 3_000_000_000


def source_time(info):
    return info["source_timestamp"] if isinstance(info, dict) else info.source_timestamp


def verify_feedback(records, raw_trace, raw_source_times):
    """Match the exact conversion in source order, independent of observer queues."""
    assert records and len(raw_trace) == len(raw_source_times), "No measured feedback provenance"
    assert all(t > 0 for t in raw_source_times), "Missing measured raw source timestamps"
    actual_times = [r["dds_source_ns"] for r in records]
    for times in (raw_source_times, actual_times):
        if any(b < a for a, b in zip(times, times[1:])):
            raise ClockReset("DDS publication clock epoch changed")
    cursor, errors = 0, []
    for record in records:
        assert record["dds_source_ns"] > 0, "Missing measured feedback source timestamp"
        matched = None
        while cursor < len(raw_trace) and raw_source_times[cursor] <= record["dds_source_ns"]:
            index = cursor
            cursor += 1
            if record["actual"] == -raw_trace[index][1]:
                matched = index
                break
        assert matched is not None, "Public feedback has no preceding measured source in sequence"
        error = abs(record["actual"] + raw_trace[matched][1])
        assert math.isfinite(error) and error <= math.pi/90, "Feedback differs from measured source"
        record["measured_index"] = matched
        record["source_ns"] = raw_trace[matched][0]
        record["raw_dds_source_ns"] = raw_source_times[matched]
        record["raw_position"] = raw_trace[matched][1]
        errors.append(error)
    return max(errors)


def restart_on_reset(setup, scenario, deadline, outcomes):
    while time.monotonic() < deadline:
        try:
            with setup() as observation:
                result = scenario(observation, deadline)
            outcomes.append({"status": "PASS"})
            return result
        except ClockReset as error:
            outcomes.append({"status": "INVALIDATED", "reason": str(error)})
    raise AssertionError("Original test budget exhausted by clock resets")


from collections import deque
from contextlib import contextmanager
import json
import os
import signal
import subprocess
import uuid


def live_members(group):
    members = []
    for entry in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = entry.read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == group and fields[0] != "Z":
                members.append(int(entry.parent.name))
        except (FileNotFoundError, ProcessLookupError):
            pass
    return members


def stop_owned(process):
    if live_members(process.pid):
        os.killpg(process.pid, signal.SIGINT)
    deadline = time.monotonic() + 10
    while live_members(process.pid) and time.monotonic() < deadline:
        process.poll()
        time.sleep(0.05)
    if live_members(process.pid):
        os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=10)
    deadline = time.monotonic() + 10
    while live_members(process.pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not live_members(process.pid), "Test-owned processes survived cleanup"


class GazeboProbe:
    def __init__(self, domain, process, env):
        import rclpy
        from rclpy.context import Context
        from rclpy.executors import SingleThreadedExecutor
        from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
        from sensor_msgs.msg import JointState
        from rosgraph_msgs.msg import Clock
        from std_msgs.msg import Float64
        from tf2_ros import Buffer, TransformListener
        self.process, self.env = process, env
        self.context = Context()
        self.context.init(domain_id=domain)
        self.node = rclpy.create_node("head_system_observer", context=self.context)
        self.executor = SingleThreadedExecutor(context=self.context)
        self.executor.add_node(self.node)
        self.samples, self.trace = deque(), []
        self.actual_trace = []
        self.raw_source_times = []
        self.last_actual_source_time = None
        self.suspend_until = None
        from ament_index_python.packages import get_package_share_directory
        from decimal import Decimal
        import xml.etree.ElementTree as ET
        world = Path(get_package_share_directory("robot_description")) / "worlds/minimal.sdf"
        step = ET.parse(world).findtext("world/physics/max_step_size")
        self.sample_period_ns = int(Decimal(step) * 1_000_000_000)
        self.actual, self.accepted, self.reference = [], [], []
        self.sim_ns = None
        self.reset = False
        self.last_sample = None
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self.node)
        qos = QoSProfile(depth=1000, reliability=ReliabilityPolicy.BEST_EFFORT,
                         durability=DurabilityPolicy.VOLATILE)
        self.raw_sub = self.node.create_subscription(JointState, "/joint_states", self.on_joint, qos)
        self.node.create_subscription(Clock, "/clock", self.on_clock, qos)
        self.actual_sub = self.node.create_subscription(Float64, "/head/pitch/actual", self.on_actual, 10)
        self.node.create_subscription(Float64, "/head/pitch/accepted", lambda m: self.accepted.append(m.data), 10)
        self.node.create_subscription(Float64, "/head_pitch_joint/reference", lambda m: self.reference.append(m.data), 10)
        self.target = self.node.create_publisher(Float64, "/head/pitch/target", 1)

    def on_clock(self, message):
        ns = message.clock.sec * 1_000_000_000 + message.clock.nanosec
        if self.sim_ns is not None and ns < self.sim_ns:
            self.reset = True
        self.sim_ns = ns

    def on_actual(self, message, info):
        stamp = source_time(info)
        if self.last_actual_source_time is not None and stamp < self.last_actual_source_time:
            self.reset = True
        self.last_actual_source_time = stamp
        self.actual.append(message.data)
        self.actual_trace.append({"actual": message.data,
            "dds_source_ns": source_time(info), "receipt_clock_ns": self.sim_ns,
            "raw_receipt_index": len(self.trace)-1})

    def on_joint(self, message, info):
        if "head_pitch_joint" not in message.name:
            raise AssertionError("Measured source lacks head_pitch_joint")
        i = message.name.index("head_pitch_joint")
        if i >= len(message.position):
            raise AssertionError("Missing head position")
        ns = message.header.stamp.sec * 1_000_000_000 + message.header.stamp.nanosec
        velocity = message.velocity[i] if i < len(message.velocity) else None
        sample = (ns, message.position[i], velocity)
        if self.last_sample is not None and ns < self.last_sample[0]:
            self.reset = True
        self.last_sample = sample
        stamp = source_time(info)
        if self.raw_source_times and stamp < self.raw_source_times[-1]:
            self.reset = True
        self.trace.append(sample)
        self.raw_source_times.append(stamp)
        if self.suspend_until is None or ns >= self.suspend_until:
            self.samples.append(sample)

    def poll(self, deadline):
        marker = os.environ.get("ROBOT_DESCRIPTION_TEST_CANCEL_FILE")
        assert not marker or not Path(marker).exists(), "Check command interrupted"
        assert self.process.poll() is None, "Head launch exited unexpectedly"
        assert time.monotonic() < min(deadline, CASE_DEADLINE.get()), "Observation deadline reached"
        self.executor.spin_once(timeout_sec=0.01)
        if self.reset:
            raise ClockReset("Simulation or DDS source clock rewound")

    def wait_for(self, predicate, deadline):
        while not predicate():
            self.poll(deadline)

    def ready(self, deadline):
        self.observation_deadline = deadline
        self.wait_for(lambda: self.sim_ns and self.last_sample and self.actual and
                      self.target.get_subscription_count(), deadline)

    def publish(self, target):
        from std_msgs.msg import Float64
        self.target.publish(Float64(data=float(target)))

    def hold(self, target, deadline, hook=None):
        deadline = min(deadline, time.monotonic() + 60)
        self.observation_deadline = deadline
        count = len(self.accepted)
        self.publish(target)
        self.wait_for(lambda: len(self.accepted) > count and self.accepted[-1] == target, deadline)
        after = self.sim_ns
        self.samples.clear()
        hold = HoldWindow(target, self.sample_period_ns)
        while True:
            self.poll(deadline)
            while self.samples:
                stamp, position, velocity = self.samples.popleft()
                if stamp <= after:
                    continue
                if hook:
                    hook(self, stamp, -position, hold)
                if hold.observe(stamp, -position):
                    assert abs(self.actual[-1] - target) <= math.pi/90, "Public actual disagrees with measured target"
                    return {"target_rad": target, "actual_rad": -position,
                            "hold_start_ns": hold.start, "hold_end_ns": stamp,
                            "hold_seconds": (stamp-hold.start)/1e9,
                            "samples": hold.samples, "final_error_rad": abs(-position-target)}

    def finish_feedback(self):
        """Freeze public observations, then drain their independently queued source."""
        if self.actual_sub is not None:
            self.node.destroy_subscription(self.actual_sub)
            self.actual_sub = None
        assert self.actual_trace, "No measured public feedback"
        cutoff = self.actual_trace[-1]["dds_source_ns"]
        self.wait_for(lambda: self.raw_source_times and self.raw_source_times[-1] >= cutoff,
                      self.observation_deadline)

    def reset_world(self):
        result = subprocess.run(["gz", "service", "-s", "/world/minimal/control",
            "--reqtype", "gz.msgs.WorldControl", "--reptype", "gz.msgs.Boolean",
            "--timeout", "5000", "--req", "reset: {all: true}"],
            env=self.env, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0 and "true" in result.stdout, result.stdout + result.stderr

    def close(self):
        self.executor.shutdown()
        self.node.destroy_node()
        self.context.shutdown()


@contextmanager
def head_simulation(tmp_path, report, launch_args=None):
    from domain_coordinator import domain_id
    attempt = len(report.setdefault("launches", [])) + 1
    log_path = tmp_path / f"launch-{attempt}.log"
    with domain_id() as domain:
        env = dict(os.environ, ROS_DOMAIN_ID=str(domain),
                   GZ_PARTITION=f"head-test-{uuid.uuid4().hex}",
                   ROS_LOG_DIR=str(tmp_path / f"ros-{attempt}"))
        def interrupted(signum, frame):
            raise KeyboardInterrupt(f"Test interrupted by {signum}")
        old_term = signal.signal(signal.SIGTERM, interrupted)
        old_int = signal.getsignal(signal.SIGINT)
        probe = None
        with log_path.open("w") as output:
            process = subprocess.Popen(["ros2", "launch", "robot_head", "head_control.launch.py",
                "gui:=false", *(launch_args or [])], env=env, stdout=output,
                stderr=subprocess.STDOUT, start_new_session=True)
            entry = {"process_group": process.pid, "domain": domain,
                     "partition": env["GZ_PARTITION"], "log": str(log_path)}
            report["launches"].append(entry)
            try:
                probe = GazeboProbe(domain, process, env)
                yield probe
            finally:
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                try:
                    stop_owned(process)
                    entry["cleanup"] = "PASS"
                    if probe:
                        (tmp_path / f"trace-{attempt}.json").write_text(json.dumps(probe.trace))
                        (tmp_path / f"actual-{attempt}.json").write_text(json.dumps(probe.actual_trace))
                        (tmp_path / f"source-times-{attempt}.json").write_text(json.dumps(probe.raw_source_times))
                        probe.close()
                finally:
                    signal.signal(signal.SIGINT, old_int)
                    signal.signal(signal.SIGTERM, old_term)


def write_report(tmp_path, report, error=None):
    report["result"] = "FAIL" if error else "PASS"
    if error:
        report["error"] = f"{type(error).__name__}: {error}"
    path = tmp_path / "head-report.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False))
    print(f"HEAD REPORT {path}\n{json.dumps(report, indent=2)}", flush=True)


from contextvars import ContextVar
from functools import wraps
CASE_DEADLINE = ContextVar("head_test_deadline", default=float("inf"))


def restarting_test(phases):
    """Restart direct scenarios with fresh paths and one original case budget."""
    def decorate(test):
        @wraps(test)
        def run(tmp_path):
            deadline = time.monotonic() + 60 * phases
            outcomes = []
            @contextmanager
            def setup():
                attempt = tmp_path / f"attempt-{len(outcomes)+1}"
                attempt.mkdir()
                token = CASE_DEADLINE.set(deadline)
                try:
                    yield attempt
                finally:
                    CASE_DEADLINE.reset(token)
            try:
                return restart_on_reset(setup, lambda path, limit: test(path), deadline, outcomes)
            finally:
                (tmp_path / "restart-report.json").write_text(json.dumps(outcomes, indent=2))
        return run
    return decorate
