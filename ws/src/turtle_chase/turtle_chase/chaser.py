"""Makes turtle2 chase turtle1, or run away from it, depending on /chase_mode."""
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtle_interfaces.msg import Mode

# must match the publisher's QoS, or we never receive the latched mode
LATCHED = QoSProfile(
    depth=1,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    reliability=ReliabilityPolicy.RELIABLE,
)

WORLD_MIN = 0.0
WORLD_MAX = 11.088  # turtlesim's canvas is ~11 x 11 units


def wrap(angle):
    """Squash any angle into -pi..pi so the turtle turns the short way around."""
    return math.atan2(math.sin(angle), math.cos(angle))


def flee_heading(mx, my, theta, lx, ly, look, margin, samples=32):
    """Pick the direction that ends up farthest from turtle1 without hitting a wall.

    Imagine taking a step of length `look` in each of `samples` directions.
    Throw away any step that would leave the safe area near the walls.
    Of the rest, keep the one that ends farthest from turtle1.
    A tiny bonus for directions close to where we already face stops it
    flip-flopping between two equally good choices.
    """
    best, best_score = None, -math.inf
    for i in range(samples):
        a = 2 * math.pi * i / samples
        nx = mx + look * math.cos(a)
        ny = my + look * math.sin(a)
        if not (WORLD_MIN + margin <= nx <= WORLD_MAX - margin and
                WORLD_MIN + margin <= ny <= WORLD_MAX - margin):
            continue  # this step would go into a wall
        score = math.hypot(nx - lx, ny - ly) - 0.1 * abs(wrap(a - theta))
        if score > best_score:
            best, best_score = a, score
    return best  # None only if every direction hits a wall


class Chaser(Node):
    def __init__(self):
        super().__init__('chaser')

        # tuning knobs, all overridable with --ros-args -p name:=value
        self.declare_parameter('catch_distance', 0.6)    # chase: stop when this close
        self.declare_parameter('resume_chase', 1.0)      # chase: start again past this
        self.declare_parameter('safe_distance', 4.5)     # flee: stop when this far
        self.declare_parameter('resume_flee', 3.8)       # flee: start again inside this
        self.declare_parameter('max_speed', 2.5)
        self.declare_parameter('turn_gain', 5.0)
        self.declare_parameter('wall_margin', 0.5)       # flee: stay this far from walls
        self.declare_parameter('flee_lookahead', 1.5)    # flee: how far ahead to test each direction

        self.leader = None   # latest turtle1 Pose
        self.me = None       # latest turtle2 Pose
        self.chase = True    # default until the mode publisher speaks up
        self.moving = True

        self.create_subscription(Pose, '/turtle1/pose', self.on_leader, 10)
        self.create_subscription(Pose, '/turtle2/pose', self.on_me, 10)
        self.create_subscription(Mode, 'chase_mode', self.on_mode, LATCHED)
        self.cmd_pub = self.create_publisher(Twist, '/turtle2/cmd_vel', 10)

        # the control loop: 20 times a second, decide how turtle2 should move
        self.create_timer(0.05, self.step)

    # ---- callbacks just store the newest data ----
    def on_leader(self, msg):
        self.leader = msg

    def on_me(self, msg):
        self.me = msg

    def on_mode(self, msg):
        if msg.chase != self.chase:
            self.chase = msg.chase
            self.moving = True  # new mode, re-evaluate from scratch
            self.get_logger().info('now ' + ('CHASING' if self.chase else 'RUNNING AWAY'))

    def p(self, name):
        return self.get_parameter(name).value

    # ---- the actual brain ----
    def step(self):
        if self.leader is None or self.me is None:
            return  # haven't heard from both turtles yet

        dx = self.leader.x - self.me.x
        dy = self.leader.y - self.me.y
        dist = math.hypot(dx, dy)

        # hysteresis: two thresholds instead of one, so it doesn't jitter on/off
        if self.chase:
            if self.moving and dist < self.p('catch_distance'):
                self.moving = False
            elif not self.moving and dist > self.p('resume_chase'):
                self.moving = True
        else:
            if self.moving and dist > self.p('safe_distance'):
                self.moving = False
            elif not self.moving and dist < self.p('resume_flee'):
                self.moving = True

        cmd = Twist()
        if not self.moving:
            self.cmd_pub.publish(cmd)  # all zeros = stand still
            return

        if self.chase:
            # point straight at turtle1
            heading = math.atan2(dy, dx)
            speed = min(self.p('max_speed'), 1.5 * dist)  # slow down as we close in
        else:
            # don't just point away from turtle1, that drives into walls and corners.
            # test a ring of directions and take the best escape that stays on the map
            heading = flee_heading(self.me.x, self.me.y, self.me.theta,
                                   self.leader.x, self.leader.y,
                                   self.p('flee_lookahead'), self.p('wall_margin'))
            if heading is None:
                heading = math.atan2(WORLD_MAX / 2 - self.me.y, WORLD_MAX / 2 - self.me.x)  # head for the middle
            speed = self.p('max_speed')

        error = wrap(heading - self.me.theta)

        # turn toward the heading, proportional to how far off we are
        cmd.angular.z = max(-6.0, min(6.0, self.p('turn_gain') * error))
        # only drive forward when roughly facing the right way (cos < 0 = facing away)
        cmd.linear.x = speed * max(0.0, math.cos(error))

        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = Chaser()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
