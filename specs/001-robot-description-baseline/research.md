# Research
- **Decision:** Keep `gz sdf -p` only in the check script. **Evidence:** malformed
  XML returned 255 in this environment. **Alternative:** reimplement graph/parser
  validation in Python, rejected as redundant.
- **Decision:** Use ament_cmake_pytest and CTest labels. **Evidence:** installed
  macro supports standard pytest JUnit results, environment and timeout settings;
  CTest properties can add the gazebo label. pytest is already installed.
  **Alternative:** launch_testing, rejected because it is not installed and this
  scope only needs one fixture-managed process plus direct ROS observations.
- **Decision:** Read installed package assets via ament_index_python, not relative
  source paths. **Rationale:** catches missing installation entries.
- **Decision:** Use `domain_coordinator.domain_id()` (installed) plus a UUID Gazebo
  partition. **Rationale:** avoids normal developer-domain traffic and coordinates
  concurrent tests. As with standard ROS test isolation, arbitrary manually chosen
  domains outside the coordinator must not be shared with the reserved test domain.
  Gazebo partition isolation: https://gazebosim.org/api/transport/13/classgz_1_1transport_1_1NodeOptions.html
- **Decision:** Observe clock/joints/TF, then query the model in the same isolated
  simulation. **Alternative:** source-text assertions on bridge YAML and node lists
  would not prove that configured integration works.
- **Decision:** Use current-run colcon XML and nonzero failure status, and check
  expected registrations before running. **Evidence:** installed `colcon test`
  offers `--return-code-on-test-failure`; `test-result` offers `--delete-yes`.
- **Decision:** 60-second observation / 10-second graceful cleanup. **Evidence:**
  explicitly agreed by the user in this chat. No physical timing requirements.
