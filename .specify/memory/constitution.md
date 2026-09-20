<!--
Sync Impact Report (temporary amendment review material; remove before committing)
Version change: unratified scaffold -> 1.0.0 (initial adoption).
Modified principles: placeholder principles replaced by the 13 supplied principles:
1. Simulation First
2. Hardware Independence
3. Simulation and Physical Robot Must Share Interfaces
4. Modular ROS 2 Architecture
5. Define Interfaces Before Implementation
6. Incremental Development
7. Testability and Observability
8. Explicit Coordinate and Naming Conventions
9. Configuration Over Hardcoding
10. Physical Safety
11. Prefer Simple Solutions
12. Specification Discipline
13. Definition of Done
Added sections: Core Principles, Project Context, Compliance Review, and populated Governance.
Removed sections: unused scaffold placeholders and example comments only.
Follow-up TODOs: none. No non-governance intents were included in the supplied input.
Only the constitution was updated; templates and commands consume it at runtime.
-->

# Robot Project Constitution

## Core Principles

### 1. Simulation First

Any new robot functionality that can reasonably be simulated MUST first be implemented and validated in ROS 2 / Gazebo.

Physical hardware SHOULD NOT be required to develop the core control logic.

Exceptions are allowed only for functionality that fundamentally depends on real hardware.

### 2. Hardware Independence

High-level robot logic MUST NOT directly depend on specific hardware such as ESP32 boards, motors, servos, or sensors.

Hardware components MUST be integrated through clearly defined ROS 2 interfaces, including:

* topics;
* services;
* actions;
* parameters;
* hardware interfaces.

Replacing a physical component SHOULD NOT require rewriting the robot's high-level behavior.

### 3. Simulation and Physical Robot Must Share Interfaces

The simulated robot and the physical robot SHOULD use the same ROS 2 interfaces whenever possible.

For example, movement commands SHOULD NOT differ depending on whether the target is the Gazebo model or the physical motors.

Differences between simulation and hardware MUST be isolated at the driver, adapter, or hardware-interface level.

### 4. Modular ROS 2 Architecture

Each major subsystem MUST have a clear and limited responsibility.

The preferred architectural separation is:

* `robot_description` — geometry, URDF/Xacro, links, and joints;
* simulation — Gazebo-specific configuration and integration;
* drive/control — robot movement and motion control;
* head — head motion and servo control;
* sensors — sensor integration and processing;
* hardware — communication with physical electronics;
* behavior — high-level robot behavior.

Packages MUST NOT become generic containers for unrelated functionality.

### 5. Define Interfaces and Verification Before Implementation

Before implementing a new subsystem or substantial feature, the following MUST be defined:

* inputs;
* outputs;
* ROS 2 interfaces;
* component responsibility;
* dependencies;
* acceptance criteria;
* how each acceptance criterion can be verified.

Acceptance criteria MUST describe observable and objectively verifiable behavior.

If expected behavior, tolerances, failure handling, or verification conditions are unclear,
they MUST be clarified during specification rather than guessed during implementation.

Internal implementation may change without changing the external contract whenever reasonably possible.

### 6. Incremental Development

Functionality MUST be implemented in small, complete, verifiable increments.

The preferred development sequence is:

simulation → basic control → feedback → physical hardware → refinement.

Multiple interdependent and unvalidated subsystems SHOULD NOT be implemented simultaneously unless necessary.

Each development step SHOULD leave the project in a working state.

### 7. Testability and Observability

System behavior MUST be observable and verifiable.

Substantial features MUST define a verification strategy derived from their requirements
and acceptance criteria.

Logic that can reasonably be tested independently SHOULD have automated tests.

ROS 2 nodes SHOULD expose enough information for debugging and verification through:

* topics;
* logs;
* TF;
* diagnostics;
* Gazebo state;
* ROS command-line tools.

Simulation behavior SHOULD be verified through measurable state rather than visual inspection alone whenever practical.

### 8. Explicit Coordinate and Naming Conventions

Names for links, joints, frames, topics, nodes, and packages MUST be consistent and descriptive.

Coordinate frames SHOULD follow ROS REP conventions unless there is a documented reason not to.

Changes to public names SHOULD be treated as interface changes.

### 9. Configuration Over Hardcoding

Physical and behavioral parameters that may require adjustment MUST NOT be unnecessarily hardcoded.

Examples include:

* robot dimensions;
* wheel or track geometry;
* maximum velocities;
* PID coefficients;
* servo limits;
* sensor thresholds.

Such values SHOULD be stored in URDF/Xacro, ROS parameters, or configuration files depending on their purpose.

### 10. Physical Safety

Commands sent to the physical robot MUST respect hardware limitations.

The system MUST enforce appropriate limits for:

* velocity;
* acceleration;
* servo position;
* motor commands.

Loss of communication, invalid commands, or critical failures MUST NOT result in uncontrolled robot movement.

Failsafe behavior MUST be considered whenever physical actuators are involved.

### 11. Prefer Simple Solutions

The first version of the robot SHOULD use the simplest architecture that satisfies the current requirements.

Do not introduce unnecessary abstraction layers, distributed architectures, optimization systems, or complex frameworks without a demonstrated need.

The architecture SHOULD allow future development without being designed around hypothetical distant requirements.

### 12. Specification Discipline

Every substantial new capability SHOULD have its own Spec Kit specification.

Specifications SHOULD primarily define required behavior, constraints, and acceptance criteria rather than prescribing implementation details unnecessarily.

Minor bug fixes, refactoring, small configuration changes, and trivial adjustments do not require separate specifications.

### 13. Definition of Done

A feature is considered complete only when:

* the project builds successfully with `colcon build`;
* relevant automated tests pass;
* required ROS 2, Gazebo, or hardware validation has been performed;
* existing functionality remains operational;
* the new functionality can be launched or executed reproducibly;
* every acceptance criterion has a defined verification method and is satisfied;
* any behavior that remains unverified is explicitly documented;
* relevant documentation and configuration are updated;
* simulation and physical-hardware behavior do not diverge without an explicitly documented reason.

## Project Context

The current development environment is Ubuntu 24.04 in WSL2, ROS 2 Jazzy,
and Gazebo Harmonic. The project root is `/home/george/robot_ws`.
The existing `robot_description` package provides the robot geometry prototype.
The preferred subsystem separation above guides future changes; it does not mandate
an immediate package reorganization.

## Compliance Review

Each substantial capability MUST be reviewed against these principles during specification,
planning, and completion. Plans MUST identify applicable interfaces, validation steps,
and any justified exceptions. Completion reviews MUST record evidence for the Definition
of Done, including build results and the applicable acceptance criteria.

MUST and MUST NOT express requirements. SHOULD and SHOULD NOT express defaults that
allow a documented exception when the feature's constraints justify it. This flexibility
covers hardware-only behavior, impractical automated tests, and other cases explicitly
qualified by the principles; it is not permission to silently omit validation.

## Governance

This constitution defines the architectural and development principles of the project.

Specifications, implementation plans, tasks, and code SHOULD comply with these principles.

If a specific feature requires violating one of these principles, the reason MUST be explicitly documented in the corresponding specification or implementation plan.

The constitution may evolve as the project develops, but changes SHOULD be deliberate and justified rather than made only to accommodate the current implementation.

Amendments MUST describe the proposed change, its rationale, and its impact on existing
specifications and implementation plans. The project maintainer MUST accept the amendment
before it becomes governing policy. A feature-specific exception MUST be documented in its
specification or plan and reviewed for its effect on interfaces, validation, and physical safety.

Constitution versions follow semantic versioning: MAJOR for incompatible principle removals
or redefinitions, MINOR for added principles or materially expanded guidance, and PATCH for
clarifications that do not change obligations. Each amendment MUST update the version and
last-amended date while preserving the original ratification date.

**Version**: 1.0.0 | **Ratified**: 2026-09-17 | **Last Amended**: 2026-09-17
