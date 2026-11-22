"""Read authoritative head constraints from the robot description."""
from dataclasses import dataclass
import math
import xml.etree.ElementTree as ET

@dataclass(frozen=True)
class Limits:
    lower: float
    upper: float
    velocity: float
    effort: float

def load_limits(path):
    try:
        joint = ET.parse(path).find("joint[@name='head_pitch_joint']")
        if joint is None or joint.get("type") != "revolute":
            raise ValueError("Missing revolute head_pitch_joint")
        if (joint.find("parent").get("link"), joint.find("child").get("link")) != ("base_link", "head_link"):
            raise ValueError("Unexpected head connectivity")
        if [float(x) for x in joint.find("axis").get("xyz").split()] != [0, 1, 0]:
            raise ValueError("Expected +Y head axis")
        element = joint.find("limit")
        limits = Limits(*(float(element.get(key)) for key in ("lower", "upper", "velocity", "effort")))
    except (AttributeError, TypeError, ET.ParseError, OSError) as error:
        raise ValueError(f"Invalid head model: {error}") from error
    values = (limits.lower, limits.upper, limits.velocity, limits.effort)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Non-finite head limits")
    if not (limits.lower < limits.upper and limits.lower <= 0 <= limits.upper and limits.velocity > 0 and limits.effort > 0):
        raise ValueError("Invalid head limits")
    return limits
