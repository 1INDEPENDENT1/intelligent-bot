# Head Pitch Control — Implementation Evidence

MG90S follow-up, 2026-11-22: **PASS — fast/full gates and independent evidence review accepted.**
See the latest section for the adjusted settings and retained evidence. The
2026-11-18 results below describe the previous settings.

Final status, 2026-11-18: **PASS — independently reviewed and accepted for simulation.**

| Gate | Observed result |
| --- | --- |
| `./scripts/check.sh` |64 reported results,0 errors/failures/skips. |
| `./scripts/check.sh --full` |84 reported results,0 errors/failures/skips;17 head physical cases. |
| Targeted provenance/echo correction |2 cases passed in33.33s. |
| `git diff --check` |Passed during implementation; repeated at final bookkeeping. |

Durable final evidence: `log/head_control_validation/release-2026-11-18/` under
repository root. It contains all17 successful physical reports, complete raw and
public/source metadata traces, invalidated-attempt artifacts, xUnit files and
fast/full/targeted logs. Counts include CTest wrappers; this is not84 distinct
robot behaviors. All initial and corrected source policy/ROS tests ran in the
final gates. No implementation commit or remote publication was made.

The sections below are a chronological development record. Earlier pending,
failed and interrupted statuses describe those attempts; the final table above
supersedes their gate status. Failed intermediate logs were not relabeled as passes.

## Initial state and execution decisions

- Existing feature branch `codex/001-head-control`; pre-existing AGENTS.md,
  memory.md and feature documents preserved. Working in the user-selected checkout.
- Requirements checklist: 16 checked, zero unchecked; no extension hooks configured.
- Baseline `./scripts/check.sh`: 10 reported results, zero failures/skips (includes wrappers).
- Native force PID and raw joint semantics retained. Reference speed scale is a
  configurable 0.5 of URDF maximum, within the plan's at-most-V bound, to leave
  margin for physical tracking; URDF constraints are unmodified.
- Dependency check attempt: `rosdep` is not present on PATH; dependency availability
  will be checked by installed package resolution/build/runtime and recorded below.

## Test-first evidence

- Policy/model/generated-model tests initially failed because implementation
  modules were absent, then passed: 24 focused cases.
- ROS adapter tests failed on missing head_pitch_node; launch override test failed
  because only gui was declared. After implementation, 35 combined focused
  policy/ROS/description cases passed.
- Four hold/reset-evaluator tests failed because helpers were absent, then passed:
  the policy suite increased to 28 cases. Covers just-under/exact 3s, excursions,
  invalid samples, duplicate/rewound time, fresh attempts and original deadline.

## First physical aiming run

`python3 -m pytest src/robot_head/test/test_head_gazebo.py -k targets -q -s`
passed (one case, two deselected) in 38.64 wall seconds. Seven targets/reversals
0,+15,-15,0,-15,+15,0 each completed a continuous >=3 simulation-second hold
within ±2 degrees. Actual position/velocity stayed inside original URDF limits;
existing TF paths were present. Details: `/tmp/head-aiming.log` and its printed
head-report.json/trace paths. Further lifecycle/negative/full verification pending.

## Remaining work

Complete reset and boundary/lifecycle/negative cases, runner registration,
reproduction docs, fast/full checks and independent reviewer. No hardware tested.

## Reset cases and infrastructure debugging

Both real Gazebo world-reset cases passed (`-k clock_reset`, 36.95 wall seconds):
reset during travel and partial hold each produced INVALIDATED then PASS, exactly
two fresh launches, no pre-reset hold credit, and owned-group cleanup.

A boundary run exposed a test-client defect: publishing integer 0 into Float64
aborted the Python process in the ROS C serializer. This left its test-owned
launch alive; its reserved domain was released by the abort, and a concurrent
focused run then observed cross-traffic. Confirmed ownership from PID/PGID,
command line and `GZ_PARTITION=head-test-*` before stopping only that group.
Fixed the test publishing boundary with `float(target)`. Focused rerun using the
project Cyclone environment: 39 policy/ROS/description cases passed. Another
failed assertion came from inspecting stringified launch substitution objects;
replaced it with direct launch-wiring capture, checking both real selected paths.

The disabled-actuator negative test initially failed because the composed head
launch always generated an actuator even when a model override was requested.
Added optional preconfigured `model_file` to the head launch (empty/default still
generates the controller). This diagnostic override allows the existing passive
URDF to prove accepted targets cannot substitute for actual joint motion. No
installed asset is modified. Corrected negative and boundary runs are pending.

## Completed automated gates

- `./scripts/check.sh`: PASS, 56 reported results, 0 errors/failures/skips,
  no Gazebo in this mode. (`/tmp/head-fast.log`.)
- `./scripts/check.sh --full`: PASS, 66 reported results, 0 errors/failures/skips,
  both packages built; baseline simulation and all seven head system cases ran.
  (`/tmp/head-full.log`, current CTest/colcon reports under build and log.)
- Counts include CTest wrappers, not 66 distinct robot behaviors. Current fast
  suite includes 33 policy/helper cases, 10 ROS interface cases, plus baseline
  description/runtime checks. Full mode adds physical and negative scenarios.
- Physical boundary/recovery and disabled-actuator targeted rerun: PASS, two
  cases in 36.04s (`/tmp/head-boundary-negative-green.log`). The later full run
  also verified publisher loss and nonzero adapter shutdown in the boundary case.
- Required head CTest registrations and gazebo label are checked by check.sh;
  both package test results are nonempty and failures propagate.

### Physical reports from the complete run

- `/tmp/pytest-of-george/pytest-18/test_boundaries_invalid_recove0/head-report.json`: PASS; invalid_inputs_rejected=5, publisher_loss_retains_target=PASS, adapter_shutdown=PASS
- `/tmp/pytest-of-george/pytest-18/test_clock_reset_restarts_only0/head-report.json`: PASS;
- `/tmp/pytest-of-george/pytest-18/test_clock_reset_restarts_only1/head-report.json`: PASS;
- `/tmp/pytest-of-george/pytest-18/test_disabled_actuator_cannot_0/head-report.json`: PASS;
- `/tmp/pytest-of-george/pytest-18/test_head_targets_hold_and_fee0/head-report.json`: PASS; position_velocity_limits=PASS
- `/tmp/pytest-of-george/pytest-18/test_interruption_and_early_ex0/head-report.json`: PASS; interruption_cleanup=PASS, early_exit_detection=PASS
- `/tmp/pytest-of-george/pytest-18/test_missing_joint_feedback_ca0/head-report.json`: PASS;

### Acceptance coverage

| Criterion | Performed evidence |
| --- | --- |
| AC-01–04 | Seven actual measured body-relative targets/reversals, each >=3s in ±2 degrees; policy tests cover sign and slew. |
| AC-05 | Existing simulator JointState is the sole raw measurement source; locked/passive model accepts target but cannot pass nonzero motion. No ground-body comparison. |
| AC-06–07 | Named sample validation/conversion, no fabricated output; real actual feedback and original TF paths checked during aiming. |
| AC-08 | Both exact URDF boundaries, actual position/velocity traces within limits, original force-mode saturation ±0.5 and unchanged SDF limits. |
| AC-09 | Five invalid physical command cases plus unit/ROS rejection at exact/next-representable boundaries, warnings and valid recovery. |
| AC-10 | Neutral startup, publisher disappearance retains target, replacement during motion, nonzero adapter shutdown/no post-shutdown reference; travel/partial-hold reset invalidates then fresh hold passes. |
| AC-11 | Nonempty fast/full gates, disabled-actuator/missing-feedback negatives, wrong-sign/>2-degree/short-hold evaluator negatives, real SIGTERM cleanup and early launch exit. |

### Environment / measurement limits

`rosdep` CLI is unavailable and sudo is not passwordless. Declared ROS runtime,
build and test dependencies were resolved with ament_index; both packages built
and real runtime tests passed. python3-yaml is importable and used by launch.
No dependency was silently treated as installed by a successful empty test run.
Applied actuator torque is not independently measured: force-mode PID saturation
configuration and the pinned native force-command path establish the configured
effort bound; JointState wrench is not claimed as actuator torque. No hardware
was exercised. GUI reproduction and independent review status are recorded below.

## GUI reproduction

`python3 log/head_gui_reproduction.py` passed with GUI-enabled Gazebo (`gz sim -r`,
without server-only `-s`), active ROS feedback and a measured neutral >=3s hold.
The launched process group was cleaned. Report/log: `/tmp/head-gui.log` and its
printed `/tmp/head-gui-check-*/head-report.json`. This proves GUI-mode launch and
control reproduction; visual rendering quality was not inspected, and no separate
visual pitch claim is made for the featureless head sphere.

## Independent review

Pending reviewer assessment. This feature is not declared complete yet.

## Independent review correction wave

Reviewer requested changes for duplicate-invalid/missing-stream hold acceptance
and absent real-transition public/raw pairing. See review.md. Nominal initial
holds remained supported by the reviewer: every one had3,001 consecutive1ms
samples, so these findings concern verifier robustness rather than fabricated
nominal movement. Red regressions were added, then36 policy cases passed after
correction. Missing-gap continuity derives from world physics max_step_size;
no arbitrary sensor-age tolerance was introduced. Two additional real scenarios
now exercise partial-hold feedback interruption/recovery and corrupted actual
feedback rejection. Final fast/full gates and scoped re-review are pending.

## Post-review association investigation

The first corrected full gate `/tmp/head-full-reviewed.log` FAILED:71 results,
3 failures (aiming and boundary physical cases plus their wrapper),0 errors/skips.
The latest-receipt raw/public pairing was invalid under topic queue skew; reviewer
matched apparent worst discrepancies to actual raw measurements205ms/870ms later
in the observer queue. No tolerance was widened. All observed aiming public values
existed in the raw trace; exact source association was missing.

Added a red regression for queue skew and causal/future-only source matching, then
changed verification to monotonic raw-source sequence association with DDS source
publication timestamps. Focused suite:37 policy/helper cases PASS. Public API and
controller code unchanged. Raw/public source metadata and resolved associations
are persisted for audit. Targeted live rerun and final full gate are pending.

## Source metadata compatibility and audit separation

The first targeted source-metadata run failed (two cases,12.24s) because this
Jazzy rclpy supplies message info as a dictionary rather than an attribute object.
Added a compatible accessor and regression;38 policy/helper cases now pass.
Raw source audit traces are retained even when intentionally interrupting the
hold consumer, so genuine public actual values remain correlatable without
crediting the missing interval toward the hold. Live aiming/corrupted-actual
checks passed in the ongoing targeted rerun; interruption recovery is finishing.
Final full gate remains pending; failed intermediate logs are retained.

## Source epoch rule

The completed targeted source-association run had1failed,2passed: aiming crossed
a DDS wall/source timestamp rewind. Supersedes the provisional note above that
live aiming had passed; that note was written before the complete log arrived.
The raw/public values agreed, but cross-epoch publication ordering was invalid.

Both callbacks and the offline matcher now invalidate timestamp-epoch rewinds.
All physical scenarios restart only the affected test under the original finite
budget, with independent attempt paths. Two epoch regressions observed red then
green; focused policy/helper suite now40 PASS. No source-error tolerance was
relaxed; future-only source matches remain rejected. Final gates are running.

## Test granularity ruling for environmental clock corrections

The next full run repeatedly invalidated the long combined aiming case on DDS
source epoch corrections at roughly8–25 simulation seconds. Restart behavior
worked, but the combined~32s sequence could not finish before another correction.
Gracefully interrupted only the owned head pytest process; the interrupted run
at `/tmp/head-full-final.log` reports a missing-result error, not a pass.

Parameterized neutral and six direction/return cases, with a full3s hold at each
precondition and target. Split both exact boundary cases from publisher loss and
adapter shutdown.17 physical cases are collected. This changes retry granularity,
not acceptance scope. Rewinds still invalidate/restart only the affected case
within its original finite budget. Final gates now use `/tmp/head-fast-complete.log`
and `/tmp/head-full-complete.log`; prior failed/interrupted runs remain historical.

## Final scope and verification interpretation

Actual head pitch is measured relative to the body, not the ground. Seven
independent neutral/aim/reversal/return parameter cases establish each initial
pose and target with a continuous3-simulation-second ±2-degree hold. Other cases
cover both boundaries, resets, invalid recovery, publisher loss, adapter shutdown,
feedback interruption/recovery, corrupted feedback, disabled actuation and owned
process cleanup. Source clock rewinds invalidate only the affected test attempt;
all attempts share its original finite wall budget.

Raw/public topic queues are independently delayed. Freeze the finite public audit
and drain raw provenance through its source watermark before source-order matching.
Match exact adapter conversion with publication-before-actual causality only within
one continuous timestamp epoch. Preserve the original ±2-degree acceptance band;
no broader error threshold was introduced to hide synchronization failures.

Implementation ruling: rosdep CLI resolution cannot run in this environment.
Instead, resolve every declared ROS dependency with ament_index, import Python
runtime dependencies, build both packages and exercise real runtime interfaces.
This verifies this installed environment, not package-index installation resolution.
The unavailable rosdep check is explicitly reported; no user approval was inferred
for system package changes. Hardware, independent actuator-torque measurement and
visual rendering inspection remain unperformed; configured force-PID saturation,
measured joint position/velocity and GUI-enabled launch are the demonstrated scope.

## Final independent acceptance

The reviewer independently audited retained release artifacts and recommends
acceptance, with no remaining source/evidence blocker.21 measured holds met
3s/±2degrees/1ms continuity;103,583 public/raw associations met conversion/order/
causality checks. Accepted traces max|q|0.5883029280rad and max|v|0.4748671193rad/s.
No ground-position criterion was used. Current GUI launch with the corrected
hold/feedback verifier passed and is retained under the release evidence `gui/`.
Rendering appearance is uninspected. Documentation wording is reconciled to
independent transition cases; no runtime change occurred after the passing gates.
See review.md for the independent verdict and the limitation scope above.


## MG90S configuration follow-up — 2026-11-22

User requested MG90S settings and selected 10 degrees/s commanded reference
speed. The launch YAML now uses reference_speed_scale=0.17453292519943295
with the retained 1 rad/s URDF velocity cap. Reference travel is 1.5 seconds
per 15 degrees and 3 seconds per 30-degree reversal; actual motion/settling is
not a timing guarantee. The head effort ceiling is now 0.1765 N m, rounded
down from the manufacturer's 4.8 V stall torque (1.8 kgf cm = 0.1765197 N m).
Joint geometry/axis/position range, PID gains and ROS contracts are retained.
These settings supersede the 0.5 speed scale / 0.5 N m values in older evidence.

Test-first observations: the updated installed-URDF torque assertion failed
against the old 0.5 N m value; both new configured-motion cases failed against
the old 0.5 rad/s reference. After settings changed, all 43 policy cases passed.
The new cases check both signs, 10 degrees after one second, arrival at
15 degrees after 1.5 seconds, endpoint retention and a three-second reversal.
Existing generated-model assertions verify effort saturation follows the URDF.

| Gate | Observed result on adjusted settings |
| --- | --- |
| ./scripts/check.sh | PASS: 66 reported results, zero errors/failures/skips. |
| ./scripts/check.sh --full | PASS: 86 reported results, zero errors/failures/skips; 17 physical head cases. |
| Independent focused source review | Accepted source and retained evidence; no blocking findings. |

Counts include six CTest wrapper results; the full gate covers 80 pytest cases.
The full headless suite retains the existing actual body-relative +/-2 degree
criterion for three continuous simulation seconds, including reversals, exact
boundaries, lifecycle/recovery/negative cases and affected-case clock-reset
restart. No tolerance, hold rule, finite budget or feedback-provenance check was
relaxed for the lower torque or slower reference.

Durable evidence: log/head_control_validation/mg90s-2026-11-22/ contains fast.log,
full.log, summary.json, test-results/ and physical/. The physical directory has
17 unique case reports (all PASS), raw/public/source-time traces, launch logs,
reset-attempt records and cleanup evidence. Pytest '*current' aliases were
excluded from the retained copies/counts to avoid duplicate case evidence.

Limitations: no physical servo driver, PWM calibration, acceleration profile,
real-servo load/accuracy/continuous-duty assessment or new GUI visual inspection.
This is a simplified simulation with a stall-based torque ceiling, not a
calibrated electromechanical MG90S model. Applied actuator torque has not been
independently measured; configured force saturation is the demonstrated scope.
Manufacturer source: https://towerpro.com.tw/product/mg90s-3/ (checked 2026-11-22).


Independent final evidence acceptance (2026-11-22): reviewer audited all 17
unique physical cases, 21 >=3-second holds inside +/-2 degrees (maximum sample
gap 1 ms), and 122,335 exact, ordered, causal raw-to-actual feedback associations.
Accepted trace maxima: absolute position approximately 0.588303 rad, absolute
velocity approximately 0.206939 rad/s (11.9 degrees/s), within retained URDF
limits. The latter is actual tracking speed: the selected 10 degrees/s is a
reference slew, not a strict cap on measured joint velocity. Reset retries and
recorded cleanup passed. No blocking or non-blocking finding remains in this
follow-up; physical-servo and applied-torque limitations above remain applicable.
