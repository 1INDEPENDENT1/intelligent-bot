"""Pure body-relative target policy. ROS and Gazebo adapters are separate."""
import math

class HeadPolicy:
    def __init__(self, limits, reference_speed_scale=1.0):
        if not math.isfinite(reference_speed_scale) or not 0 < reference_speed_scale <= 1:
            raise ValueError("reference_speed_scale must be in (0, 1]")
        self.limits = limits
        self.speed = limits.velocity * reference_speed_scale
        self.target = 0.0
        self.reference = 0.0
        self.previous_ns = None

    def accept(self, pitch):
        if not math.isfinite(pitch) or not self.limits.lower <= -pitch <= self.limits.upper:
            return False
        self.target = -pitch
        return True

    def advance(self, stamp_ns):
        if self.previous_ns is not None and stamp_ns > self.previous_ns:
            step = self.speed * (stamp_ns - self.previous_ns) / 1e9
            delta = self.target - self.reference
            self.reference += max(-step, min(step, delta))
            self.reference = max(self.limits.lower, min(self.limits.upper, self.reference))
        self.previous_ns = stamp_ns
        return self.reference

def measured_pitch(names, positions):
    try:
        value = positions[names.index("head_pitch_joint")]
        return -value if math.isfinite(value) else None
    except (ValueError, IndexError):
        return None
