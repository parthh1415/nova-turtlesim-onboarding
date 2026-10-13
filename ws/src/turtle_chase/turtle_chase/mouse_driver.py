"""Drives turtle1 toward your mouse pointer while it's over the TurtleSim window."""
import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

from Xlib import X, display as xdisplay

WORLD_SIZE = 11.088  # turtlesim world units across the whole canvas


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def window_title(win, net_wm_name):
    """Read a window's title. Qt apps set _NET_WM_NAME, older apps set WM_NAME."""
    try:
        prop = win.get_full_property(net_wm_name, 0)
        if prop and prop.value:
            v = prop.value
            return v.decode(errors='ignore') if isinstance(v, bytes) else str(v)
        name = win.get_wm_name()
        if isinstance(name, bytes):
            name = name.decode(errors='ignore')
        return name or ''
    except Exception:
        return ''


def is_real_window(win):
    """Skip Qt's hidden helper windows: must be visible and bigger than a few pixels."""
    try:
        attrs = win.get_attributes()
        geo = win.get_geometry()
    except Exception:
        return False
    return attrs.map_state == X.IsViewable and geo.width > 50 and geo.height > 50


def find_window(win, title, net_wm_name):
    """Depth-first search of the X window tree for the visible window titled exactly `title`."""
    if window_title(win, net_wm_name).strip() == title and is_real_window(win):
        return win
    try:
        children = win.query_tree().children
    except Exception:
        return None
    for child in children:
        hit = find_window(child, title, net_wm_name)
        if hit is not None:
            return hit
    return None


class MouseDriver(Node):
    def __init__(self):
        super().__init__('mouse_driver')

        self.declare_parameter('window_title', 'TurtleSim')
        self.declare_parameter('max_speed', 3.0)
        self.declare_parameter('turn_gain', 6.0)
        self.declare_parameter('arrive_distance', 0.15)

        # connect to the X server named by $DISPLAY (XQuartz on your Mac)
        self.x = xdisplay.Display()
        self.net_wm_name = self.x.intern_atom('_NET_WM_NAME')
        self.window = None
        self.target = None  # (x, y) in turtle world units
        self.pose = None

        self.create_subscription(Pose, '/turtle1/pose', self.on_pose, 10)
        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        self.create_timer(0.05, self.step)    # 20 Hz control loop
        self.create_timer(1.0, self.locate)   # keep looking until the window exists

    def p(self, name):
        return self.get_parameter(name).value

    def on_pose(self, msg):
        self.pose = msg

    def locate(self):
        if self.window is not None:
            return
        root = self.x.screen().root
        self.window = find_window(root, self.p('window_title'), self.net_wm_name)
        if self.window is None:
            self.get_logger().info('waiting for the TurtleSim window...', throttle_duration_sec=5.0)
        else:
            self.get_logger().info('found the TurtleSim window, move your mouse over it')

    def read_pointer(self):
        """Pointer position in turtle world coords, or None if it's off the window."""
        try:
            ptr = self.window.query_pointer()
            geo = self.window.get_geometry()
        except Exception:
            self.window = None  # window closed or changed, go find it again
            return None
        if not ptr.same_screen:
            return None
        px, py = ptr.win_x, ptr.win_y
        if not (0 <= px < geo.width and 0 <= py < geo.height):
            return None
        # pixels -> world units. screen y grows DOWN, turtle y grows UP, so flip it
        wx = px / geo.width * WORLD_SIZE
        wy = (geo.height - py) / geo.height * WORLD_SIZE
        return wx, wy

    def step(self):
        if self.window is None or self.pose is None:
            return

        tgt = self.read_pointer()
        if tgt is not None:
            self.target = tgt  # pointer off the window = keep heading to the last spot

        cmd = Twist()
        if self.target is not None:
            dx = self.target[0] - self.pose.x
            dy = self.target[1] - self.pose.y
            dist = math.hypot(dx, dy)
            if dist > self.p('arrive_distance'):
                error = wrap(math.atan2(dy, dx) - self.pose.theta)
                cmd.angular.z = max(-8.0, min(8.0, self.p('turn_gain') * error))
                cmd.linear.x = min(self.p('max_speed'), 2.0 * dist) * max(0.0, math.cos(error))
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = MouseDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
