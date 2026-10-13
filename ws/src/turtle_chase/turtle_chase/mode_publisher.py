"""Flips turtle2 between CHASE and RUN AWAY every N seconds (default 10)."""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy

from turtle_interfaces.msg import Mode

# "latched" QoS: the last message is kept around, so a node that starts
# late still gets the current mode immediately instead of waiting up to 10s
LATCHED = QoSProfile(
    depth=1,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    reliability=ReliabilityPolicy.RELIABLE,
)


class ModePublisher(Node):
    def __init__(self):
        super().__init__('mode_publisher')

        # a parameter, so you can change the period without editing code:
        #   ros2 run turtle_chase mode_publisher --ros-args -p period:=5.0
        self.declare_parameter('period', 10.0)
        period = self.get_parameter('period').value

        self.pub = self.create_publisher(Mode, 'chase_mode', LATCHED)
        self.chase = True

        # call self.flip every `period` seconds
        self.timer = self.create_timer(period, self.flip)

        self.publish_mode()  # announce the starting mode right away

    def flip(self):
        self.chase = not self.chase
        self.publish_mode()

    def publish_mode(self):
        msg = Mode()
        msg.chase = self.chase
        self.pub.publish(msg)
        self.get_logger().info('mode -> ' + ('CHASE' if self.chase else 'RUN AWAY'))


def main():
    rclpy.init()
    node = ModePublisher()
    try:
        rclpy.spin(node)  # hand control to ROS: it calls your timer for you
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
