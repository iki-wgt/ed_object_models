cmake_minimum_required(VERSION 2.8.3)
project(ed_object_models)

## Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS
)

catkin_add_env_hooks(99.ed_object_models SHELLS bash DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/env-hooks)


###################################
## catkin specific configuration ##
###################################
catkin_package(
)
