# Independent Head-Control Review

Reviewer: `head_control_review` (read-only reviewer subagent), 2026-11-17.
**Final verdict (2026-11-18): ACCEPT simulation implementation.** Initial and
subsequent findings are resolved; no source/evidence blocker remains. Final
bookkeeping below reconciles the remaining documentation wording.

Initial verdict was REQUEST CHANGES; the historical findings/corrections follow.

## Initial findings

1. Important: hold verifier checked duplicate stamps before invalid/band checks,
   so duplicate invalid/out-of-band values could preserve partial hold. Missing
   observations could also be credited from widely separated timestamps.
2. Important: real-transition public actual/raw agreement was not recorded or
   checked; only final public actual-to-target error was asserted.
3. Minor: root README package inventory omitted robot_head; task status header
   still said generation-only despite completed checkboxes.

Reviewer independently inspected all 66 initial results and seven unique physical
reports. Nominal aiming trace independently supported all seven holds: 3,001
samples each spanning exactly 3s, maximum source gap1ms, all errors below2deg.
Observed aiming maxima: |q|0.2392067313rad and |v|0.4547039815rad/s. The reviewer
correctly distinguished these valid recorded nominal results from verifier defects.

## Corrections and evidence

- Added red regressions for duplicate-invalid/excursion, interrupted feedback,
  and public-feedback echo. New tests initially failed (nine red outcomes while
  introducing explicit cadence API); after fixes the policy/helper suite passes
  36 cases. No product tolerance was invented: cadence is derived from installed
  world max_step_size, observed as exactly1ms throughout initial full traces.
- Hold now validates before duplicate suppression and clears on missing-step gaps.
  Missing named joint is a verification error instead of a silently ignored sample.
- Public actual is paired with latest raw sample/source timestamp and receipt
  ordering, persisted to actual-*.json, and checked through real movement.
  Added real feedback-interruption recovery and corrupted-actual negative cases.
- Corrected README package table/tree/dependency and task status header.

Scoped independent re-review and final post-correction gates pending. Configured
force saturation is verified; applied torque is not independently measured.
rosdep CLI, hardware and visual rendering inspection remain unavailable/unperformed
as described in verification.md. No completion verdict is asserted yet.

## Scoped re-review progress

The same independent reviewer personally reproduced the corrected helper behavior:
invalid/out-of-band duplicates clear hold, missing gaps cannot count, and a fresh
full3s stream after recovery is required. Public/raw receipt associations and
persisted traces were inspected; documentation corrections accepted. Reviewer
also identified an orthogonality problem in the wrong-sign negative test: it
used sparse timestamps, so the missing-gap rule alone could reject even correct
angles. Corrected to identical complete0,1,2,3s cadence for bad data and a passing
valid control. Reviewer inspected that correction and reports no remaining issue
in it. Focused policy/helper rerun:36 PASS. Final physical evidence still pending.

## Source-association correction

The first post-review full run reported71 results, 3 failures (two physical cases
plus wrapper), no errors/skips. Latest-observer-receipt association compared
raw/public samples205ms and870ms apart. The reviewer independently found matching
real raw values for every aiming actual observation, so this was a verification
association defect, not evidence of a runtime sign-conversion defect.

Replaced that association with ordered exact-conversion matching against raw
source observations, enforcing DDS source-publication causality. Persist raw DDS
source timestamps and resolved measured indices/stamps. A queue-skew/future-only
regression was red before correction;37 focused policy/helper tests now pass.
The updated live aiming/corrupted-feedback checks and final full run are pending.
The failed log `/tmp/head-full-reviewed.log` is retained; it is not a passing gate.

## Measurement epoch handling

The next targeted run passed corrupted-feedback and interrupted-stream cases but
failed aiming at a DDS source wall-clock rewind of about2.2s. Exact values still
matched actual raw state. Reviewer independently diagnosed the epoch boundary;
causal timestamps cannot be compared across that reset. This failed targeted
run remains recorded at `/tmp/head-association-fixed.log` (1failed,2passed).

Added raw/public DDS rewind regressions (two red, then green), detect rewind in
callbacks and in offline association, and restart only the affected test from
fresh setup. Direct system scenarios now share a bounded per-case restart wrapper
with new attempt paths and one original deadline; source-clock and simulation
resets cannot join measurement epochs.40 policy/helper cases pass. Final fast/
full logs are `/tmp/head-fast-final.log` and `/tmp/head-full-final.log`, pending.

## Case-granularity adjustment

The combined aiming case repeatedly restarted correctly on environmental DDS
wall-clock corrections before it could finish. Its owned pytest was gracefully
interrupted, with missing-result status retained in the log. Split aims into seven
independent parameter cases and boundaries/lifecycle into three independent cases,
without weakening initial/target holds, source association or limits.17 physical
cases now represent the same acceptance scope. Scoped reviewer assessment and
fresh complete gate outcomes are pending.

## Final independent verdict — 2026-11-18

Reviewer accepts simulation implementation after inspecting retained release data:
64 fast results and84 full results,0 errors/failures/skips;78 pytest cases plus
6 wrappers. All17 physical cases passed. Independently audited21 holds across13
positive scenarios: each>=3 simulation seconds, all samples within2degrees,
maximum source gap1ms. Audited103,583 persisted actual/raw associations with exact
conversion, increasing measured index and raw DDS publication before feedback.
Observed accepted trace maxima:|q|0.5883029280rad,|v|0.4748671193rad/s, within the
original limits. Reset reports include INVALIDATED,INVALIDATED,PASS as expected
when environmental corrections add retries. All recorded launch cleanup passes.
Current GUI-mode reproduction also passes; appearance is not visually inspected.

The reviewer found no remaining implementation/evidence blocker. Final minor
wording about a combined simulation was corrected in plan.md and quickstart.md
without runtime changes. Required docs/tasks/memory reconciled. rosdep resolution,
hardware and independently measured applied torque remain explicitly unverified;
configured saturation and installed dependency/build/runtime evidence are the
verified scope. No unresolved non-blocking code finding remains.


## MG90S configuration follow-up verdict — 2026-11-22

The independent reviewer accepted the focused source change and then the
retained simulation evidence. No blockers, requirement gaps, weak/missing tests
within scope or architecture/interface issues were identified. Verified correct
4.8 V stall-torque conversion and URDF-derived 0.1765 N m saturation, configured
10 degrees/s reference, both-direction timing/reversal regressions, and unchanged
ROS contracts/position/velocity bounds. This reference is not an actual-speed cap.

Evidence in log/head_control_validation/mg90s-2026-11-22/: fast66/full86 reported
results, zero errors/failures/skips; 17 unique physical cases PASS; 21 holds each
>=3 continuous simulation seconds in +/-2 degrees, maximum gap1ms; 122,335 exact,
ordered and causal feedback associations. Accepted trace maxima approximately
|q|0.588303 rad and |v|0.206939 rad/s (11.9 degrees/s), within retained limits.
Reset retries and launch cleanup also passed. Accept the simulation settings
follow-up. Physical MG90S behavior, continuous-duty capacity and independently
measured applied actuator torque remain unverified. No new GUI visual inspection.
