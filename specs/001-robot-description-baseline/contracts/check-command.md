# Check command contract
- `./scripts/check.sh` or `./scripts/check.sh --fast`: convert, build, source
  overlay, run fast registered tests, report current results; explicitly exclude
  simulation verification.
- `./scripts/check.sh --full`: same checks plus the registered Gazebo test.
- `--help`: describe modes without building or launching.
- Unknown or excess arguments: nonzero status and usage; no build or simulation.
- Any command/test failure: nonzero exit, no success message. Test results are
  printed even after assertion failures. Zero baseline registration is a failure.
- Mode changes must not reuse stale test results. Cleanup removes generated test
  result files under this workspace's build tree only.
- Tests use the built installed package and preserve current robot interfaces.
- `colcon test` directly runs both registered test groups; the script adds the
  conversion/build gate and mode selection.
