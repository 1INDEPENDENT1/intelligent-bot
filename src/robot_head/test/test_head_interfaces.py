"""Real ROS graph contract tests without Gazebo."""
import math
from pathlib import Path
import pytest
import rclpy
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from domain_coordinator import domain_id
from std_msgs.msg import Float64
from sensor_msgs.msg import JointState
from rosgraph_msgs.msg import Clock
from robot_head.head_pitch_node import HeadPitchNode
import time

@pytest.fixture
def graph():
    with domain_id() as domain:
        context = Context()
        context.init(domain_id=domain)
        controller = HeadPitchNode(context=context)
        client = rclpy.create_node("head_test_client", context=context)
        executor = SingleThreadedExecutor(context=context)
        executor.add_node(controller)
        executor.add_node(client)
        try:
            yield controller, client, executor
        finally:
            executor.shutdown()
            controller.destroy_node()
            client.destroy_node()
            context.shutdown()

def until(executor, predicate, seconds=10):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        executor.spin_once(timeout_sec=0.02)
        if predicate():
            return
    raise AssertionError("Expected ROS observation missing")

def clock(ns):
    msg = Clock()
    msg.clock.sec, msg.clock.nanosec = divmod(ns, 1_000_000_000)
    return msg

def test_target_reference_and_rewind(graph):
    controller, client, executor = graph
    target = client.create_publisher(Float64, "/head/pitch/target", 1)
    ticks = client.create_publisher(Clock, "/clock", qos_profile_sensor_data)
    refs, accepted = [], []
    client.create_subscription(Float64, "/head_pitch_joint/reference", lambda m: refs.append(m.data), 1)
    client.create_subscription(Float64, "/head/pitch/accepted", lambda m: accepted.append(m.data), 1)
    until(executor, lambda: target.get_subscription_count() and ticks.get_subscription_count())
    target.publish(Float64(data=math.pi/12))
    until(executor, lambda: bool(accepted))
    assert accepted[-1] == pytest.approx(math.pi/12)
    ticks.publish(clock(1_000_000_000))
    until(executor, lambda: bool(refs))
    ticks.publish(clock(1_200_000_000))
    until(executor, lambda: refs[-1] < 0)
    last = refs[-1]
    ticks.publish(clock(0))
    until(executor, lambda: controller.policy.previous_ns == 0)
    assert controller.policy.target == pytest.approx(-math.pi/12)
    assert controller.policy.reference == last

@pytest.mark.parametrize("invalid", [1.0, -1.0, float("nan"), float("inf"), -float("inf")])
def test_invalid_target_preserves_destination(graph, invalid):
    controller, client, executor = graph
    target = client.create_publisher(Float64, "/head/pitch/target", 1)
    until(executor, lambda: target.get_subscription_count() > 0)
    target.publish(Float64(data=0.2))
    until(executor, lambda: controller.policy.target == -0.2)
    target.publish(Float64(data=invalid))
    until(executor, lambda: controller.rejected_commands == 1)
    assert controller.policy.target == -0.2
    target.publish(Float64(data=-0.1))
    until(executor, lambda: controller.policy.target == 0.1)

def test_feedback_comes_from_named_measurement_only(graph):
    controller, client, executor = graph
    measured = client.create_publisher(JointState, "/joint_states", qos_profile_sensor_data)
    actual = []
    client.create_subscription(Float64, "/head/pitch/actual", lambda m: actual.append(m.data), 1)
    until(executor, lambda: measured.get_subscription_count() > 0)
    assert actual == []
    measured.publish(JointState(name=["head_pitch_joint"], position=[]))
    until(executor, lambda: controller.invalid_measurements == 1)
    assert actual == []
    measured.publish(JointState(name=["other", "head_pitch_joint"], position=[1.0, -0.2]))
    until(executor, lambda: bool(actual))
    assert actual[-1] == 0.2
    measured.publish(JointState(name=["head_pitch_joint"], position=[float("nan")]))
    until(executor, lambda: controller.invalid_measurements == 2)
    assert actual == [0.2]

def test_bad_startup_path_is_error():
    context = Context()
    context.init()
    try:
        with pytest.raises(ValueError):
            HeadPitchNode(context=context, parameter_overrides=[Parameter("model_file", value="/missing/head.urdf")])
    finally:
        context.shutdown()


def test_publisher_loss_retains_target_and_shutdown_sends_no_neutral(graph):
    controller, client, executor = graph
    target = client.create_publisher(Float64, "/head/pitch/target", 1)
    ticks = client.create_publisher(Clock, "/clock", qos_profile_sensor_data)
    accepted = []
    client.create_subscription(Float64, "/head/pitch/accepted", lambda m: accepted.append(m.data), 1)
    until(executor, lambda: target.get_subscription_count() and ticks.get_subscription_count())
    target.publish(Float64(data=0.2))
    until(executor, lambda: accepted == [0.2])
    client.destroy_publisher(target)
    ticks.publish(clock(1_000_000_000))
    until(executor, lambda: controller.policy.previous_ns == 1_000_000_000)
    ticks.publish(clock(2_000_000_000))
    until(executor, lambda: controller.policy.reference == -0.2)
    assert controller.policy.target == -0.2
    assert accepted == [0.2]
    executor.remove_node(controller)
    controller.destroy_node()
    until(executor, lambda: client.count_publishers("/head/pitch/accepted") == 0)
    assert accepted == [0.2]


def test_target_replacement_during_motion_is_latest_valid(graph):
    controller, client, executor = graph
    target = client.create_publisher(Float64, "/head/pitch/target", 1)
    ticks = client.create_publisher(Clock, "/clock", qos_profile_sensor_data)
    until(executor, lambda: target.get_subscription_count() and ticks.get_subscription_count())
    target.publish(Float64(data=0.2))
    until(executor, lambda: controller.policy.target == -0.2)
    ticks.publish(clock(1_000_000_000))
    until(executor, lambda: controller.policy.previous_ns == 1_000_000_000)
    ticks.publish(clock(1_050_000_000))
    until(executor, lambda: controller.policy.reference < 0)
    target.publish(Float64(data=-0.2))
    until(executor, lambda: controller.policy.target == 0.2)
    ticks.publish(clock(1_150_000_000))
    until(executor, lambda: controller.policy.reference > 0)
