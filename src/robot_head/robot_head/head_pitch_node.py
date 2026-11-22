"""ROS policy adapter; actual feedback always comes from the simulator."""
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import Float64
from sensor_msgs.msg import JointState
from rosgraph_msgs.msg import Clock
from robot_head.model import load_limits
from robot_head.policy import HeadPolicy, measured_pitch

class HeadPitchNode(Node):
    def __init__(self, **kwargs):
        super().__init__("head_pitch", **kwargs)
        default_model = str(Path(get_package_share_directory("robot_description")) / "urdf/robot.urdf")
        self.declare_parameter("model_file", default_model)
        self.declare_parameter("reference_speed_scale", 1.0)
        try:
            limits = load_limits(self.get_parameter("model_file").value)
            self.policy = HeadPolicy(limits, self.get_parameter("reference_speed_scale").value)
        except ValueError:
            self.destroy_node()
            raise
        self.rejected_commands = 0
        self.invalid_measurements = 0
        self.reference_pub = self.create_publisher(Float64, "/head_pitch_joint/reference", 1)
        self.accepted_pub = self.create_publisher(Float64, "/head/pitch/accepted", 1)
        self.actual_pub = self.create_publisher(Float64, "/head/pitch/actual", 1)
        self.create_subscription(Float64, "/head/pitch/target", self.on_target, 1)
        self.create_subscription(Clock, "/clock", self.on_clock, qos_profile_sensor_data)
        self.create_subscription(JointState, "/joint_states", self.on_measurement, qos_profile_sensor_data)
        self.accepted_pub.publish(Float64(data=0.0))

    def on_target(self, message):
        if self.policy.accept(message.data):
            self.accepted_pub.publish(Float64(data=message.data))
        else:
            self.rejected_commands += 1
            self.get_logger().warning(f"Rejected head_pitch_joint target {message.data!r}: non-finite or outside limits")

    def on_clock(self, message):
        stamp = message.clock.sec * 1_000_000_000 + message.clock.nanosec
        self.reference_pub.publish(Float64(data=self.policy.advance(stamp)))

    def on_measurement(self, message):
        pitch = measured_pitch(message.name, message.position)
        if pitch is None:
            self.invalid_measurements += 1
            self.get_logger().warning("Invalid head_pitch_joint measurement: missing name/position or non-finite value")
            return
        self.actual_pub.publish(Float64(data=pitch))

def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = HeadPitchNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
