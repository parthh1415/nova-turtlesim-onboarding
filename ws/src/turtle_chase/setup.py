import os
from glob import glob
from setuptools import setup

package_name = 'turtle_chase'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        # lets ROS find this package by name
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # copies every launch file so `ros2 launch turtle_chase ...` works
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Parth Srivastava',
    maintainer_email='dal601310@utdallas.edu',
    description='Nova onboarding turtlesim nodes',
    license='MIT',
    entry_points={
        # "ros2 run turtle_chase <name>" -> which function to call
        'console_scripts': [
            'mode_publisher = turtle_chase.mode_publisher:main',
            'chaser = turtle_chase.chaser:main',
            'mouse_driver = turtle_chase.mouse_driver:main',
        ],
    },
)
