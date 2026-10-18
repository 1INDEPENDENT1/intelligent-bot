## Testing and Verification

Testing is part of the SDD process and starts during specification, not after implementation.

### Specification and Acceptance Criteria

The user is not expected to manually define acceptance criteria.

Start from the user's desired outcome in natural language and derive:

- functional requirements;
- acceptance criteria;
- happy paths;
- boundary cases;
- failure cases;
- observable results.

Ask clarification questions only when an unresolved decision materially affects
behavior, interfaces, safety, limits, error handling, or verification.

Do not ask the user for information that can reasonably be derived from the
repository, existing specifications, or project context.

Do not invent arbitrary tolerances, timing requirements, limits, or failure behavior.
If such a value is necessary and cannot be derived, ask for clarification.

### During Specify

Every substantial requirement must be testable.

For each feature, determine:

- what behavior is being added;
- what observable result is expected;
- how success and failure can be distinguished;
- important boundary and invalid-input cases;
- whether the behavior can be verified automatically;
- what requires ROS 2, Gazebo, or physical hardware to verify.

Acceptance criteria must be concrete enough to become tests or explicit verification procedures.

If a requirement cannot be objectively verified, clarify it before implementation.

During specification, ask questions when needed, for example:

- What exact result should this command produce?
- What tolerance is acceptable?
- What should happen outside the valid range?
- What should happen on startup, shutdown, timeout, or loss of communication?
- Which output/topic/state proves that the feature worked?
- Does this behavior need to work identically in simulation and on real hardware?
- Can this requirement be covered by an automated test?

Do not invent unspecified expected behavior only to make a test possible.

### During Plan

For each acceptance criterion, define the appropriate verification level and testing approach.

Prefer the lowest-cost test that can reliably prove the requirement:

1. Unit test
2. ROS 2 integration test
3. Gazebo/system test
4. Physical hardware test

The plan should identify which requirements are covered at which level.

Examples:

- calculations, limits, conversions, state logic → unit tests;
- node inputs/outputs and ROS interfaces → ROS 2 integration tests;
- joints, movement, TF, controllers, simulated sensors → Gazebo/system tests;
- electrical behavior or real actuator/sensor behavior → hardware tests.

### During Implementation

Implement the required tests or verification procedures together with the feature.

- test pure logic with unit tests where possible;
- test ROS 2 interfaces and node behavior with integration tests;
- use Gazebo tests for measurable simulated behavior;
- add regression tests for fixed bugs when practical;
- preserve existing tests;
- do not rely only on visual inspection when behavior can be measured.

### Completion

Before a feature is considered complete:

- every acceptance criterion must have a verification method;
- relevant automated tests must pass;
- required simulation or hardware checks must be performed;
- unverified behavior must be explicitly reported.

A successful build alone does not prove that a feature works.