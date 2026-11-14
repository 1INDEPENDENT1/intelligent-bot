# Test data and observations
No production data model is added.
- **Installed description:** package share path, required files, mesh references.
- **Model contract:** documented links, joint parent/child/type, head axis and limits.
  Limits must be finite; lower < upper; effort and velocity > 0.
- **Runtime observation:** at least two clock values with an increase, a named head
  joint with finite position, expected TF paths, and the spawned model.
- **Run result:** selected mode, executed tests, failures, evidence and exclusions.
Lifecycle: initialize isolated test context -> launch -> observe or fail -> cleanup
on every exit -> report. Any missing condition remains a failure, not a skipped test.
