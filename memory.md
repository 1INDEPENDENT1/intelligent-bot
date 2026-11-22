# Project Memory

Persistent context for work in `robot_ws`. Read and update this file according to
the `Project Memory` section in [AGENTS.md](AGENTS.md). This is a concise record
of material events, not a transcript or a replacement for project specifications.

## Context References

- [README.md](README.md): product concept, current development stage, environment,
  and entry points for building and checking the project.
- [Project constitution](.specify/memory/constitution.md): architectural principles
  and project constraints.
- [Baseline specification](specs/001-robot-description-baseline/spec.md),
  [plan](specs/001-robot-description-baseline/plan.md), and
  [tasks](specs/001-robot-description-baseline/tasks.md): baseline requirements,
  implementation approach, and task tracking.
- [Package README](src/robot_description/README.md): robot model, ROS interfaces,
  validation procedures, and limitations.

## Entry Format

```markdown
### YYYY-MM-DD — Event type: short title
- Event: what changed, was decided, or was learned.
- Reason: why this matters for future work.
- Evidence: relevant files, explicit user decision, or commands and actual results.
- Limitations / next steps: unverified behavior, blockers, or remaining work; use
  "None" when there is nothing to record.
```

Dates use Europe/Moscow. Add events below in chronological order. Earlier events
describe what was known at the time; check later entries and current source files
before relying on them.

## Event Log

### 2026-11-09 — Context: starting point from existing documentation
- Event: README.md describes a compact tracked companion robot developed with
  ROS 2 Jazzy and Gazebo Harmonic on Ubuntu 24.04 in WSL2/WSLg. The current baseline
  has fixed track envelopes and a passive head pitch joint; locomotion, head
  actuation, sensors, and physical hardware integration remain future work.
  Cyclone DDS is the documented project middleware default.
- Reason: preserve an entry point for future sessions without treating planned
  capabilities as implemented behavior.
- Evidence: README.md, read on 2026-11-09. The README also records a successful
  Cyclone DDS simulation check on 2026-11-06; that is a historical documented
  result, not a fresh verification in this session.
- Limitations / next steps: this entry summarizes documentation; it does not
  independently verify runtime behavior. Consult current source and specifications
  before changing or claiming capabilities.

### 2026-11-09 — Decision: keep project memory in the repository
- Event: the user requested `memory.md` and a rule for recording events. Created
  this file and added reading and recording instructions to AGENTS.md.
- Reason: retain useful decisions, findings, verification evidence, and unfinished
  work across project sessions.
- Evidence: explicit user request in this chat; memory.md and the `Project Memory`
  section of AGENTS.md.
- Limitations / next steps: recording is an agent workflow instruction, not a
  background logger. Verification of this documentation change is pending and
  will be recorded as a separate event after the checks run.

### 2026-11-09 — Verification: project memory documentation
- Event: reviewed memory.md and the AGENTS.md addition for the reading rule,
  material-event triggers, entry format, evidence requirements, and preservation
  of prior entries. The project fast checks passed.
- Reason: verify the documentation change and record actual check results for
  future sessions; this resolves the pending verification in the preceding entry.
- Evidence: `git diff --check` passed. `./scripts/check.sh` ran in WSL Ubuntu-24.04
  using `rmw_cyclonedds_cpp` and returned exit code 0: URDF-to-SDF conversion,
  build, and test-registration checks passed; colcon reported 10 tests, 0 errors,
  0 failures, and 0 skipped. That total includes CTest wrapper results, as described
  in README.md; it is not a count of distinct robot behaviors.
- Limitations / next steps: the default fast check excludes Gazebo; simulation
  and physical hardware were not exercised in this session. No runtime code was
  changed. Future sessions must follow AGENTS.md to maintain this memory.

### 2026-11-14 — Specification: head pitch control draft
- Event: created `specs/001-head-control/spec.md` and its requirements-quality
  checklist; selected that directory in `.specify/feature.json`. Retained the
  existing `codex/001-head-control` branch and the explicitly requested directory
  name despite the existing baseline feature sharing prefix `001`.
- Reason: define physical head movement, upward-positive operator angles,
  actual-state feedback, joint constraints, and verification before implementation.
- Evidence: current URDF uses +Y pitch with limits ±0.610865 rad, effort 0.5 N·m,
  velocity 1 rad/s; positive raw joint rotation points forward +X downward.
  Existing `/joint_states` and head TF provide feedback; the head is passive.
  Package README notes the featureless sphere cannot visibly prove pitch and
  existing smoke checks exclude settling/stability tolerances. Draft maps each
  acceptance criterion to a verification level and preserves raw feedback semantics.
- Verification: template resolved through `.specify/scripts/bash/resolve-template.sh`;
  mandatory sections, active feature JSON, and exactly three clarification markers
  verified. No `.specify/extensions.yml` exists, so pre/post hooks were skipped.
  `./scripts/check.sh` returned 0: 10 reported tests, 0 errors/failures/skips
  (includes CTest wrappers). `git diff --check` passed before this memory entry.
- Limitations / next steps: draft awaits user decisions on invalid-input/lifecycle
  policy, timing/hold criterion, and measurable body stability; checklist deliberately
  leaves related items unchecked. Resolve before planning. No runtime implementation,
  Gazebo run, hardware check, or independent implementation review was performed.

### 2026-11-14 — Decision: head control acceptance policies confirmed
- Event: user answered all three pending questions: reject out-of-range and
  non-finite targets, start neutral, retain the last valid target while running;
  no speed guarantee with bounded verification; compare body movement against
  an identical no-command simulation. Updated FR-004–006 and the clarification
  record; all 16 requirements-quality checklist items now pass.
- Reason: replaces the unresolved policies in the preceding draft entry with
  explicit user decisions and makes the specification ready for planning.
- Evidence: user answers in this chat; `specs/001-head-control/spec.md` and
  `checklists/requirements.md`. Structural validation confirms 10 functional
  requirements, no remaining clarification markers, and 16 checked quality items.
- Limitations / next steps: `$speckit-plan` must define the ROS interface contract,
  bounded test procedure, and reproducible body/reference comparison before code.
  Fast checks passed as recorded above; runtime head-control behavior remains
  unimplemented and unverified. No simulation or hardware validation was run.

### 2026-11-15 — Planning: head pitch control design
- Event: generated `specs/001-head-control/plan.md`, `research.md`, `data-model.md`,
  `contracts/ros-interfaces.md`, and `quickstart.md` on `codex/001-head-control`.
  Chose native Gazebo force PID with URDF-derived ±effort saturation and a separate
  `robot_head` ROS policy adapter: upward-positive radian target/actual, preserved
  raw JointState/TF, latest valid target, measured-state feedback and slew reference.
- Reason: define interfaces, subsystem ownership and every acceptance verification
  before implementation without introducing controller-manager infrastructure.
- Evidence: read-only research found installed gz-sim8 8.11.0, physics7 7.6.0,
  available native plugin, and preserved URDF constraints on SDF conversion. Fixed
  reduction makes the simulated head parent `base_footprint`; independent pose
  measurement must account for that. Pinned primary sources linked in research.md.
  Research agent's design consistency check found no blocking contradiction;
  incorporated caveat that ROS acceptance does not identify Gazebo actuation step.
- Verification: `./scripts/check.sh` returned 0: 10 reported tests, 0 errors,
  failures or skips (includes wrappers); fast mode excludes Gazebo. Five design
  artifacts and required plan sections present, no unresolved template placeholders;
  `git diff --check` passed. No `.specify/extensions.yml`, so no pre/post hooks.
- Limitations / next steps: planning only; runtime code unchanged. `$speckit-tasks`
  is next. Tune PID and prove actual motion/limits and strict paired body stability
  in implementation; reference comparison may reveal reaction/solver effects and
  must not acquire arbitrary tolerance. Reuse baseline 60s wall observation/10s
  cleanup budgets. No head-control simulation, hardware check, or independent
  completed-feature reviewer assessment has been performed.

### 2026-11-15 — Task generation: head pitch implementation breakdown
- Event: generated `specs/001-head-control/tasks.md` from the current spec, plan,
  research, data model, ROS contract and quickstart. All 36 tasks remain unchecked:
  US1 physical aiming 10, US2 measured feedback 5, US3 limits/lifecycle 7, shared
  setup/foundation/final gates 14. Thirteen tasks identify conditional parallel
  opportunities with file/dependency boundaries; no agents were spawned.
- Reason: make implementation executable in story increments with tests before
  behavior, explicit dependency order, AC-01–11 / FR-001–010 coverage, paired
  no-command body verification and independent completed-feature review gates.
- Evidence: setup-tasks.sh resolved the active feature and template; validation
  confirmed 36 sequential IDs, unchecked checklist syntax, paths, correct story
  labels, required phases and no unresolved placeholders/trailing whitespace.
  `git diff --check` passed. No extensions.yml exists, so pre/post hooks skipped.
- Limitations / next steps: documentation only; no runtime tests or simulation were
  rerun for task generation and no implementation task is complete. Optional
  `$speckit-analyze` can check cross-artifact consistency before `$speckit-implement`.
  PID dynamics, physical limits and strict body comparison remain unverified;
  failed/unrepeatable comparison must be diagnosed without invented slack.

### 2026-11-16 — Analysis: head control artifacts before implementation
- Event: analyzed spec.md, plan.md, tasks.md, supporting ROS contract and
  constitution via speckit-analyze. Found I1 (HIGH): whole-run body-pose maxima
  from spawn can mask later head-induced motion below an earlier settling peak;
  I2 (MEDIUM): neutral reset on clock rewind is defined in plan/contract/tasks
  without an explicit exception in the specification's last-valid-target policy;
  U1 (MEDIUM): observation budget is bounded but transition/phase stopping rules
  are insufficiently explicit to reproduce post-arrival overshoot coverage.
- Reason: nominal requirement/task coverage does not establish that the chosen
  measurements prove the requested behavior. Address I1 before implementation;
  align reset policy and define deterministic observation endpoints as well.
- Evidence: plan.md:190–213 and tasks.md:T012/T018 (I1); spec.md:128–135,
  plan.md:131–135 and contracts/ros-interfaces.md:68–69 (I2); plan.md:168–177
  (U1). All 15 FR/SC requirements have associated work among 36 unchecked tasks;
  no zero-coverage requirements, unmapped tasks or definite constitution conflicts
  identified. No extension hooks configured; prerequisite command succeeded.
- Limitations / next steps: analysis, not runtime verification; no tests or Gazebo
  run performed. Spec, plan, tasks and contracts were not edited, and no report
  file was created. This memory entry is required by AGENTS.md despite the skill's
  read-only default. Remediation edits need a follow-up user instruction under
  the analysis workflow; rerun analysis after changes before implementation.

### 2026-11-17 — Scope correction: simplify head-control verification
- Event: user explicitly clarified that only head angle relative to the main
  body must be measured, and requested simpler tests. This supersedes the
  2026-11-14 no-command body-reference choice and the world-stability portions
  of the 2026-11-15 plan/tasks and 2026-11-16 I1 finding.
- Reason: earlier interpretation added ground-relative body-stability behavior
  beyond the intended joint-control task. Actual simulated head joint position
  directly measures head rotation relative to the body.
- Changes: updated spec, plan, research, data model, ROS contract, quickstart,
  requirements checklist and tasks under `specs/001-head-control/`. Reuse the
  existing Gazebo JointStatePublisher/ROS bridge; convert actual q to operator
  pitch -q. Removed PosePublisher/world-pose reconstruction, paired neutral runs,
  body maxima and synchronized replay. Removed three obsolete tasks and
  renumbered remaining 33 unchecked tasks (US1 9, US2 5, US3 7, shared 12).
- Verification: documentation validation passed for sequential task IDs/references,
  story counts, all 11 acceptance criteria and 15 FR/SC items, and whitespace.
  `git diff --check` passed. No runtime code or tests exist for this feature yet;
  no ROS/Gazebo/hardware tests were run for this documentation-only change.
- Limitations / next steps: targets 0/+15/-15 degrees and reversals retain ±2-degree
  accuracy and original URDF limits. I1 no longer applies. U1 now uses first fresh
  in-band measured sample per target; final neutral arrival ends aiming without
  an added hold requirement. Separate I2 clock-reset policy alignment remains open
  and is flagged in plan/research/checklist; this edit does not resolve it.

### 2026-11-17 — Decision: continuous hold and clock-reset test restart
- Event: user specified that the affected test should restart on clock reset,
  and each expected head angle must remain in its allowed band for 3 seconds
  before passing. Updated spec, plan, tasks, research, data model, ROS contract,
  quickstart and requirements checklist under `specs/001-head-control/`.
- Reason: replaces first-in-band-sample acceptance from the preceding entry and
  resolves the remaining I2/U1 policy/procedure inconsistencies in the documents.
- Contract: use actual body-relative head pitch within ±2 degrees for 3 continuous
  simulation seconds; out-of-band/invalid samples clear the hold, pauses/stale
  feedback cannot advance it. Reset invalidates/discards the current attempt and
  restarts only that affected test from fresh setup. Original finite case budget
  (derived from existing phase budgets) is shared across attempts; exhaustion
  fails rather than looping or passing. Fresh controller startup remains neutral;
  a timestamp rewind alone does not overwrite the running controller's target.
- Evidence: explicit user decision in this chat. Documentation validation passed:
  33 sequential unchecked tasks/references, all 11 ACs and 15 FR/SC items, aligned
  hold/reset rules in seven design documents, all 16 quality checklist items
  reviewed, and `git diff --check`. Tasks include short/exact holds, band exit and
  re-entry, paused/stale feedback, reset during movement/hold and retry exhaustion.
- Limitations / next steps: documentation/design only; no ROS/Gazebo/hardware
  verification or runtime implementation performed. Earlier I1 is superseded by
  simplified scope; I2/U1 now have aligned decisions, not executed test evidence.
  The task list remains entirely pending implementation and required review.

### 2026-11-17 — Re-analysis: head-control artifacts aligned
- Event: reran speckit-analyze after the user-approved scope, hold and reset
  clarifications. No actionable inconsistencies, ambiguities, material duplication,
  zero-coverage requirements or definite constitution conflicts identified.
- Reason: confirms that the previously reported I1/I2/U1 findings are resolved
  at specification/design/task level before implementation; this is not evidence
  of implemented or working head control.
- Evidence: prerequisite command succeeded; reviewed spec, plan, all 33 unchecked
  tasks, constitution and supporting data/ROS contract. All 15 FR/SC requirements
  have associated work (100% task association), with all 11 ACs mapped. Documents
  agree on actual body-relative joint pitch, ±2 degrees for 3 continuous simulation
  seconds, hold restart on band exit, invalidation/fresh affected-test restart on
  clock reset, and original finite budget shared across attempts. No pre/post
  extension hooks configured. Core artifact hashes remained unchanged by analysis.
- Limitations / next steps: only this mandatory project-memory entry was appended;
  no feature artifact/remediation edits, report file, runtime tests or simulation.
  Proceed to `$speckit-implement`; required actual fast/full checks, reset/hold
  negative tests and independent reviewer remain pending implementation tasks.

### 2026-11-17 — Implementation progress: head adapter and initial physical tests
- Event: added robot_head package, pure URDF/policy/model generation, ROS target/
  accepted/actual adapter, force-PID configuration, composed launch and optional
  baseline model-file override. Existing raw joint/TF contracts retained. Added
  policy/interface/hold/reset tests and initial isolated Gazebo acceptance suite.
- Evidence: 24 initial policy cases passed after missing-module red tests; hold
  tests observed four red cases then 28 green policy cases. Combined focused
  policy/ROS/description suite most recently passed 39 cases. Initial physical
  seven-target/reversal test passed all >=3-second holds and measured position/
  velocity limits. Real reset-during-travel and reset-during-hold cases passed,
  each INVALIDATED then fresh PASS with cleanup. See feature verification.md.
- Finding/workaround: integer zero in a test Float64 publisher caused native abort,
  leaving one owned simulation and allowing later domain cross-talk. Verified its
  ownership before cleanup; converted outgoing test targets to float. A launch
  assertion used private substitutions incorrectly; fixed its observation method.
- Limitations / next steps: boundary/negative reruns, remaining lifecycle evidence,
  documentation, final fast/full gates and independent reviewer are still pending.
  rosdep is unavailable on PATH; no hardware tested. Do not declare completion.

### 2026-11-17 — Verification progress: full head-control gates passed
- Event: completed the new head package and isolated Gazebo scenarios, updated
  runner registration and reproduction docs, and requested independent reviewer
  `head_control_review`. Thirty of 33 implementation tasks are marked complete;
  review/fixes/final record remain pending.
- Evidence: `./scripts/check.sh` passed with 56 reported results; `--full` passed
  with 66, 0 errors/failures/skips (counts include CTest wrappers). Seven unique
  physical reports cover seven-target 3s holds, travel/partial-hold reset restarts,
  boundaries/rejection/recovery, publisher loss, nonzero adapter shutdown, passive
  actuator/missing-feedback negative proofs and SIGTERM/early-exit cleanup.
  GUI-mode launch and neutral >=3s hold passed; logs/reports in verification.md.
- Reason: actual simulation evidence is available for independent completion
  assessment instead of relying only on build/static tests.
- Limitations / next steps: reviewer pending; no completion claim yet. rosdep CLI
  unavailable (sudo not passwordless); declared ROS packages resolved with ament
  and both packages build/run. Applied torque is not independently measured;
  verified native force-PID saturation/configured constraints. No hardware tested;
  GUI rendering appearance was not visually inspected. Preserve unrelated AGENTS.md.

### 2026-11-18 — Review corrections: hold continuity and feedback provenance
- Event: independent reviewer requested two important corrections: hold verifier
  could retain time through invalid duplicate/missing observations; public actual
  was compared only with target at completion, not measured raw state in motion.
  Corrected both and root package documentation/status wording. See review.md.
- Evidence: added red regressions then36 policy/helper cases passed. Hold now
  validates before duplicate suppression and clears on source gaps larger than
  installed world physics-step period (1ms, matching observed publisher cadence).
  Public actual/raw pairs now carry receipt ordering/source stamps and are checked
  and persisted throughout movement. Added live stream-interruption recovery and
  corrupted actual negative tests. Reviewer independently reproduced helper fixes
  and accepted source corrections, including a valid-control cadence correction
  to ensure angle-negative tests isolate angle errors rather than missing data.
- Reason: valid nominal traces alone did not prove verifier robustness; prevent
  false passes under invalid/missing or target-echo measurements.
- Limitations / next steps: corrected fast gate passed59 results; full corrected
  gate and final scoped reviewer evidence assessment are running/pending. No
  completion claim yet. Existing rosdep/torque/hardware/visual limits still apply.

### 2026-11-18 — Verification: corrected release gates and retained evidence
- Event: final corrected fast gate passed64 reported results and full gate passed84,
  with0 errors/failures/skips;17 head physical cases allPASS. Retained final reports,
  raw/public/source metadata, attempts, xUnit and logs under
  `log/head_control_validation/release-2026-11-18/` (ignored build evidence).
- Reason: independent review uncovered verifier gaps; final evidence must prove
  corrected behavior rather than reuse the earlier nominal pass or purged tmp data.
- Corrections: derive hold continuity from installed physics step, handle invalid
  duplicates/gaps, correlate source-ordered feedback within DDS clock epochs,
  freeze/drain audit queues before matching, restart only affected cases under
  original budgets, and split long sequences into independent transition cases.
  Same ±2-degree/3-second user criteria; controller/public interfaces unchanged.
- Evidence: `fast.log`, `full.log`, `summary.json` and copied physical artifacts in
  retained directory. Two targeted drain/isolated-echo cases passed33.33s. Reviewer
  accepted scoped source fixes; final retained-evidence audit still pending.
- Limitations / next steps: complete final reviewer verdict and task bookkeeping.
  Prior failed/interrupted runs are retained as such in verification.md. rosdep
  unavailable: installed dependencies/build/runtime checked instead. No hardware,
  independent applied-torque measurement or visual rendering inspection claimed.

### 2026-11-18 — Completion: simulated head pitch control independently accepted
- Event: completed all33 head-control tasks and final documentation. robot_head
  accepts upward-positive ROS target radians and exposes actual pitch relative
  to the body using the existing head_pitch_joint. Native force PID uses original
  URDF constraints; raw JointState/TF and passive baseline launch remain compatible.
- Evidence: final `./scripts/check.sh` PASS64 reported results and `--full` PASS84,
  0 errors/failures/skips;17 physical cases. Independent reviewer accepted source
  and audited21 >=3s holds in±2degrees with1ms maximum sample gap,103,583 causal
  actual/raw associations, limits, invalidated→fresh reset attempts and cleanup.
  Accepted trace maxima |q|0.5883029280rad, |v|0.4748671193rad/s. Current GUI-mode
  launch/neutral hold/feedback verification also PASS. `git diff --check` passed.
- Reason: actual retained simulation evidence plus resolved independent findings
  establish completion rather than merely a successful build or nominal first run.
- Artifacts: specs/001-head-control/verification.md and review.md; durable ignored
  evidence in log/head_control_validation/release-2026-11-18/ (including GUI/xUnit).
  Earlier failed/interrupted verification attempts remain identified in the record.
- Limitations / next steps: no hardware, independent applied-actuator torque or
  visual rendering inspection performed. Force saturation/configuration and actual
  joint position/velocity are verified. rosdep CLI unavailable; validated installed
  dependencies with ament/Python imports and build/runtime instead. No remaining
  blocking or non-blocking code finding. Work remains uncommitted on the existing
  feature branch; unrelated pre-existing AGENTS.md edits preserved. Launch/reproduce
  via src/robot_head/README.md. No required implementation work remains.


### 2026-11-22 — Hardware selection / MG90S specification lookup
- User identified MG90S as the planned head actuator, after finding current head motion too fast. No new target speed has been chosen and no controller setting was changed.
- Manufacturer documentation checked: https://towerpro.com.tw/product/mg90s-3/ lists 13.4 g, 22.8 x 12.2 x 28.5 mm, stall torque 1.8 kgf cm at 4.8 V (about 0.1765 N m), operating speed 0.10 s/60 degrees at 4.8 V (600 degrees/s), and 0.08 s/60 degrees at 6.0 V. Voltage information is inconsistent: operating-voltage field says 4.8 V, while speed/torque rows use 6.0/6.6 V. Confirm the exact supplied unit before specifying an upper supply voltage. Manufacturer page does not establish current draw, angular accuracy, or a calibrated pulse-to-angle range.
- Repository evidence: src/robot_head/config/head_control.yaml reference_speed_scale=0.5 and src/robot_description/urdf/robot.urdf velocity=1 rad/s give a commanded reference limit of 0.5 rad/s (28.6 degrees/s). URDF effort=0.5 N m exceeds the documented MG90S 4.8 V stall torque; existing Gazebo actuation is not a validated hardware servo model.
- Limitations / next steps: documentation lookup only; hardware speed, load capacity, supply current and +/-2 degree accuracy remain unmeasured. Hardware-informed speed/torque changes require a separate implementation decision. No runtime code changed or tests rerun.


### 2026-11-22 — Decision / implementation: MG90S simulation settings
- User requested MG90S settings and explicitly selected 10 degrees/s desired motion (15 degrees in about 1.5 seconds). This resolves the speed decision left open in the preceding lookup event.
- Changed robot_head/config/head_control.yaml reference_speed_scale from 0.5 to 0.17453292519943295, retaining the URDF 1 rad/s limit. Changed robot_description/urdf/robot.urdf head effort ceiling from 0.5 to 0.1765 N m, rounded down from the manufacturer's 4.8 V stall rating. Geometry, position range, PID gains and ROS contracts retained. Package READMEs and specs/001-head-control spec/plan/tasks record the adjustment and simulation/hardware distinctions.
- Evidence: torque regression first failed against 0.5 N m; both new configured-motion direction cases first failed against the old 0.5 rad/s reference. After adjustment all 43 policy cases passed; ./scripts/check.sh passed 66 reported results, zero errors/failures/skips. Independent head_control_review source review found no blocker. git diff --check passed (existing line-ending warnings only).
- Limitations / next steps: full Gazebo suite is still running; current changed-setting simulation acceptance is not yet complete. Reference timing is not a physical arrival guarantee. No hardware driver, acceleration profile, measured continuous-duty torque or real-servo verification was added. This is a small configuration follow-up (T034-T036), not a new subsystem.


### 2026-11-22 — Verification / review: MG90S follow-up accepted for simulation
- Completed T036: ./scripts/check.sh PASS66 reported results and --full PASS86, zero errors/failures/skips; 17 unique head physical cases. Counts include six CTest wrappers. Durable logs, xUnit, reports and traces retained in log/head_control_validation/mg90s-2026-11-22/; pytest current aliases excluded from case counts.
- Independent head_control_review accepted source and evidence with no outstanding findings: 21 continuous >=3-second holds within +/-2 degrees, max sample gap1ms; 122,335 exact/ordered/causal actual/raw associations; reset retries and cleanup passed. Accepted trace maxima approximately |q|0.588303 rad and |v|0.206939 rad/s (11.9 degrees/s), within the retained URDF bounds.
- Important distinction: user-selected 10 degrees/s is commanded reference slew, not a strict actual-speed cap; measured tracking briefly exceeds it. Documented in specs/001-head-control/verification.md and review.md. Updated source paths from preceding entry are src/robot_head/config/head_control.yaml and src/robot_description/urdf/robot.urdf.
- Limitations / next steps: simulation configuration follow-up complete; no hardware/PWM driver, acceleration profile, calibrated electromechanical model, continuous-duty validation, independently measured applied torque or new GUI visual inspection. Existing unrelated edits preserved; work remains uncommitted.


### 2026-11-22 — Commit preparation: task 001 head control
- User explicitly requested a descriptive commit of all task 001 changes. Prepared the robot_head package, description integration/MG90S joint settings, tests, check runner, Spec Kit artifacts, READMEs, ignore rules and this memory for one local commit on codex/001-head-control, titled "Implement task 001 head pitch control in Gazebo".
- Fresh pre-commit ./scripts/check.sh passed66 reported results with zero errors/failures/skips. Full simulation evidence remains the reviewed unchanged-source 86-result/17-case MG90S run recorded above; no extra simulation run was required for this commit-only request. Retained the fresh log as log/head_control_validation/mg90s-2026-11-22/precommit-fast.log.
- Preserved and excluded the separate pre-existing AGENTS.md Project Memory edit. Generated logs/build outputs remain ignored. Commit description covers ROS target/actual semantics, limits/lifecycle, 10 degrees/s reference, 0.1765 N m ceiling, validation and simulation-only limitations. No push, merge or remote publication was requested.
- Staged-content audit exposed four trailing spaces in the previously untracked historical verification record (not covered by earlier tracked-only diff checks); removed those spaces without changing recorded results. Runtime sources were unchanged.


### 2026-11-22 — Commit: task 001 locally recorded
- Created the authorized task 001 commit on codex/001-head-control with title "Implement task 001 head pitch control in Gazebo" and a detailed behavior/settings/verification description. The commit contains 34 task-related files, including source, tests, specifications, documentation and project memory.
- Evidence: successful git commit and git log confirmation; final worktree audit leaves only the preserved pre-existing AGENTS.md edit. The fresh 66-result pre-commit gate and earlier reviewed full 86-result simulation gate are recorded above. Staged whitespace check passed after the four documentation spaces were removed.
- Scope / next steps: local commit only; no push or merge. Hardware limitations remain unchanged. This completion entry is included in the same commit through amendment of the just-created local commit.
