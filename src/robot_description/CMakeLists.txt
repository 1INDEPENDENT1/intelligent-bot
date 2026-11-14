cmake_minimum_required(VERSION 3.8)

project(robot_description)

find_package(ament_cmake REQUIRED)

install(
    DIRECTORY
        urdf
        meshes
        launch
        config
        worlds
    DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
    find_package(ament_cmake_pytest REQUIRED)
    ament_add_pytest_test(test_description test/test_description.py)
    ament_add_pytest_test(test_runtime_environment test/test_runtime_environment.py)
    ament_add_pytest_test(test_gazebo_smoke test/test_gazebo_smoke.py NOCAPTURE)
    # The smoke test owns its observation deadline and process-group cleanup.
    # Do not let an outer CTest timeout kill it before its finally block runs.
    set_tests_properties(test_gazebo_smoke PROPERTIES LABELS "pytest;gazebo" TIMEOUT 0)
endif()

ament_package()
