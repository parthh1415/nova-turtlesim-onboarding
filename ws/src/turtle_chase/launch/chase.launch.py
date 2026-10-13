"""Container 2: turtle2 chases or flees turtle1, mode flips on a timer."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # lets you do:  ros2 launch turtle_chase chase.launch.py period:=5.0
    period = LaunchConfiguration('period')

    return LaunchDescription([
        DeclareLaunchArgument('period', default_value='10.0',
                              description='seconds between chase/run-away flips'),

        Node(package='turtle_chase', executable='mode_publisher', output='screen',
             parameters=[{'period': period}]),

        Node(package='turtle_chase', executable='chaser', output='screen'),
    ])
