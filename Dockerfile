# ROS 2 Humble, compiled from source, on Ubuntu 22.04 (jammy)
FROM ubuntu:jammy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# 1. locale - ROS expects UTF-8
RUN apt-get update && apt-get install -y locales \
 && locale-gen en_US en_US.UTF-8 \
 && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
 && rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# 2. add the ROS apt repo - used ONLY for build tools, ROS itself comes from source
RUN apt-get update && apt-get install -y software-properties-common curl \
 && add-apt-repository universe \
 && ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F '"tag_name"' | awk -F'"' '{print $4}') \
 && curl -L -o /tmp/ros2-apt-source.deb \
      "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb" \
 && apt-get install -y /tmp/ros2-apt-source.deb \
 && rm /tmp/ros2-apt-source.deb \
 && rm -rf /var/lib/apt/lists/*

# 3. build tools (ros-dev-tools = colcon + rosdep + vcstool)
RUN apt-get update && apt-get install -y \
      build-essential cmake git wget \
      python3-pip python3-flake8-docstrings python3-pytest-cov \
      ros-dev-tools \
 && rm -rf /var/lib/apt/lists/*

# 4. pull the Humble source code
WORKDIR /opt/ros2_humble
RUN mkdir src \
 && vcs import --input https://raw.githubusercontent.com/ros2/ros2/humble/ros2.repos src

# 5. install every system library the source tree needs (Qt for turtlesim, etc.)
RUN apt-get update \
 && rosdep init \
 && rosdep update --rosdistro humble \
 && rosdep install --from-paths src --ignore-src -y --rosdistro humble \
      --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers" \
 && rm -rf /var/lib/apt/lists/*

# 6. compile ROS 2. this is the hours-long step. lower BUILD_JOBS if it runs out of RAM
ARG BUILD_JOBS=4
RUN MAKEFLAGS="-j${BUILD_JOBS}" colcon build --merge-install \
      --parallel-workers ${BUILD_JOBS} \
      --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
 && rm -rf build log

# 7. every new shell has ROS ready to go
RUN echo "source /opt/ros2_humble/install/setup.bash" >> /root/.bashrc

# 8. extra Python libs for our own nodes. sits AFTER the big build, so adding it
#    only re-runs this one cheap layer - the ROS compile above stays cached
RUN apt-get update && apt-get install -y python3-xlib \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /ws
CMD ["bash"]
