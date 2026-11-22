# Data Model: Head Pitch Control

This is transient control state, not database storage. All angles are radians.
See [ROS interfaces](contracts/ros-interfaces.md) for wire representation.

| Entity | Fields | Validation / relationships |
| --- | --- | --- |
| Joint model | joint name, parent/child, axis, L/U/V/E | Loaded from installed URDF. Existing name/axis/connectivity preserved; finite ordered position limits include zero; V/E positive. Operator limits `[-U,-L]`. |
| Accepted target | theta, raw q=-theta, simulation epoch | Finite and inclusive limits. Starts zero. Latest accepted value replaces previous target. Invalid input leaves it unchanged. |
| Reference | q_ref, previous simulation stamp | Starts zero; advance toward q by at most V*dt per advancing simulation sample. Clock rewind rebases time without changing target/reference. Never beyond [L,U]. |
| Measurement | name, raw position q, source stamp, optional raw velocity/effort | JointState name/index/finite validation. Public actual=-q. No target-derived measurement; malformed/missing samples produce no actual output. |
| Native controller config | PID gains, force mode, initial0, cmd_min/max | Gains configurable/tested; force output bounds derived from ±E; velocity bypass disabled. |
| Verification run | test/attempt ID, target, acceptance time, raw samples, source stamps, hold_start, hold_elapsed, original deadline, outcome | Isolated attempts. Hold requires 3 continuous simulation seconds within ±2°. Reset invalidates attempt; restart affected test from fresh setup within original finite budget. Retain attempt logs. |

State progression: configuration -> neutral/awaiting clock -> tracking latest
valid target. New valid targets replace the destination; repeated targets are
idempotent. Invalid inputs warn without a transition. Command silence retains the
destination. Simulation rewind rebases timing without replacing the target/reference.
The test runner invalidates that attempt and restarts its setup; a newly started
controller initializes neutral. Shutdown stops the
adapter without publishing a replacement target.

Actual measurement is independent of this command state. A valid target or
in-band reference alone cannot produce a successful reached-target result.

Verification quantities:
- Target error: `abs(theta_actual - theta_target) <= pi/90`.
- Head angle relative to body: `theta_actual = -q` from simulator-originated
  `head_pitch_joint` position; translation/tilt of the whole model does not change q.
- Target pass: fresh measured samples stay within pi/90 for 3 continuous
  simulation seconds. Leaving the band clears hold_start; re-entry starts over.
  Paused time/stale measurements cannot advance the hold. Final neutral hold
  ends aiming. Clock reset invalidates the attempt and its accumulated hold.
- Limits: raw positions within [L,U], absolute velocity <= V; force PID output
  bounded by E. Record all sampled violations, including after first target arrival.
