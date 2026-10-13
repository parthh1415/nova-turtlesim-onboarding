"""Container 1: turtlesim window, spawn turtle2, mouse control for turtle1."""
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # the built-in simulator: opens the window and creates turtle1
        Node(package='turtlesim', executable='turtlesim_node', name='sim', output='screen'),

        # call turtlesim's built-in /spawn service to add turtle2.
        # `ros2 service call` waits until the service exists, so the order is safe
        ExecuteProcess(
            cmd=['ros2', 'service', 'call', '/spawn', 'turtlesim/srv/Spawn',
                 "{x: 2.0, y: 2.0, theta: 0.0, name: 'turtle2'}"],
            output='screen',
        ),

        # your node: turtle1 follows the mouse
        Node(package='turtle_chase', executable='mouse_driver', output='screen'),
    ])
