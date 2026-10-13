# Nova turtlesim onboarding

My solution to the Nova (UT Dallas autonomous driving) ROS 2 onboarding task.

- ROS 2 Humble compiled from source on `ubuntu:jammy`
- Container 1: turtlesim, spawns turtle2, turtle1 follows the mouse
- Container 2: turtle2 chases or runs away from turtle1, mode flips every 10s via a custom message
- Messages cross between the two containers over a shared Docker network

## Run it (macOS)

```bash
colima start --cpu 6 --memory 14
docker build --build-arg BUILD_JOBS=3 -t nova-humble .
open -a XQuartz && xhost +localhost
docker compose up -d

# tab A
docker compose exec sim bash
colcon build && source install/setup.bash
ros2 launch turtle_chase sim.launch.py

# tab B
docker compose exec chaser bash
source install/setup.bash
ros2 launch turtle_chase chase.launch.py
```

## Layout

- `Dockerfile`: ROS 2 Humble built from source
- `docker-compose.yml`: two containers on one network
- `ws/src/turtle_interfaces`: custom `Mode.msg` (chase or run away)
- `ws/src/turtle_chase`: `mouse_driver`, `chaser`, `mode_publisher` nodes and both launch files
