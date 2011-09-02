cmake_minimum_required(VERSION 2.8)

set(CMAKE_OSX_ARCHITECTURES i386)

if(EXISTS /usr/lib/libpython2.5.dylib AND EXISTS /usr/include/python2.5/)
  set(PYTHON_INCLUDE_DIRS /usr/include/python2.5)
  set(PYTHON_LIBRARIES /usr/lib/libpython2.5.dylib)
  message("Using Python 2.5")
else()
  find_package(PythonLibs REQUIRED)
endif()
include_directories(${PYTHON_INCLUDE_DIRS})

find_package(Boost REQUIRED)  
include_directories("${Boost_INCLUDE_DIRS}")
set(Boost_USE_STATIC_LIBS OFF)
set(Boost_USE_MULTITHREADED ON)
set(Boost_USE_STATIC_RUNTIME OFF)
find_package(Boost COMPONENTS python)

include_directories(/usr/include/ni)
link_libraries(/usr/lib/libOpenNI.dylib)

add_library(pynui SHARED pynui.cpp)
target_link_libraries(pynui ${Boost_LIBRARIES} ${PYTHON_LIBRARIES})

set_target_properties(pynui PROPERTIES OUTPUT_NAME "pynui" PREFIX "" SUFFIX ".so")

if(CMAKE_COMPILER_IS_GNUCXX)
  add_definitions("-Wall -Wno-attributes")
endif()
