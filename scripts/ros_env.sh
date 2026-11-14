#!/usr/bin/env bash
# Source in every project ROS terminal before starting nodes or CLI tools.
# An explicit selection remains available for middleware diagnostics.
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}"
