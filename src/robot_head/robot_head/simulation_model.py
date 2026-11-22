"""Add only the native actuator to an ephemeral copy of the description."""
import math
import xml.etree.ElementTree as ET
from robot_head.model import load_limits

COMMAND_TOPIC = "/model/my_robot/joint/head_pitch_joint/0/cmd_pos"

def generate_model(source, destination, gains):
    limits = load_limits(source)
    if set(gains) != {"p_gain", "i_gain", "d_gain"}:
        raise ValueError("Provide exactly p_gain, i_gain, d_gain; limits come from URDF")
    if not all(math.isfinite(v) and v >= 0 for v in gains.values()):
        raise ValueError("PID gains must be finite and nonnegative")
    tree = ET.parse(source)
    gazebo = ET.SubElement(tree.getroot(), "gazebo")
    plugin = ET.SubElement(gazebo, "plugin", filename="gz-sim-joint-position-controller-system",
                           name="gz::sim::systems::JointPositionController")
    values = dict(joint_name="head_pitch_joint", joint_index="0", topic=COMMAND_TOPIC,
                  initial_position="0", use_velocity_commands="false",
                  cmd_max=str(limits.effort), cmd_min=str(-limits.effort), **gains)
    for key, value in values.items():
        ET.SubElement(plugin, key).text = str(value)
    tree.write(destination, encoding="utf-8", xml_declaration=True)
