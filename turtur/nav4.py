import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import sys
import math


class Nav4(Node):
    def __init__(self, args):
        super().__init__("nav4")

        # Misc
        self.sleepy_ = self.create_rate(2.0)
        self.stop_ = Twist()
        self.stop_.linear.x = 0.0
        self.stop_.angular.z = 0.0
        self.linear_vel_ = 0.0
        self.angular_vel_ = 0.0
        self.alpha_ = 0.1
        self.path_ = []
        self.points_per_line_ = 10

        # What do
        self.mode_ = int(args[0])
        self.goal_dist_ = 1.0
        self.goal_angle_ = 0.0

        # Position
        self.x_ = None
        self.y_ = None
        self.theta_ = None
        self.prev_x_ = None
        self.prev_y_ = None
        self.prev_theta_ = None

        # Flags
        self.flipper_ = False
        self.path_calcd_ = False

        # Subscribe to odom, because that is good
        self.create_subscription(Odometry, "/odom", self.odom_callback, 1)

        # Publish to /cmd_vel
        self.vel_pub_ = self.create_publisher(Twist, "/cmd_vel", 1)
        self.info_pub_ = self.create_publisher(Float32, "/path_deviance", 1)

        # Spin my head right round right round
        self.create_timer(0.1, self._process)


    # Callbacks
    def odom_callback(self, msg):
        self.x_ = msg.pose.pose.position.x
        self.y_ = msg.pose.pose.position.y
        z = msg.pose.pose.orientation.z
        w = msg.pose.pose.orientation.w
        self.theta_ = 2*math.atan2(z, w)



    # I am creative with comments
    def thingy(self, angle):
        if not self.flipper_:
            # Calculate stuff
            self.goal_angle_ = angle
            self.prev_theta_ = self.theta_
            self.goal_dist_ -= math.sqrt((self.x_ - self.prev_x_)**2 + (self.y_ - self.prev_y_)**2)
            self.prev_x_ = self.x_
            self.prev_y_ = self.y_
            self.angular_vel_ = 0.0

            # Are we there yet
            if self.goal_dist_ <= 1e-3:
                self.vel_pub_.publish(self.stop_)
                self.flipper_ = True
                self.get_logger().info("Forward complete")
                return

            # Keep going
            msg = Twist()
            target = min(1.0, max(self.goal_dist_, 0.0))
            self.linear_vel_ += self.alpha_ * (target - self.linear_vel_)
            msg.linear.x = self.linear_vel_
            self.vel_pub_.publish(msg)

        elif self.flipper_:
            # Calculate stuff
            self.goal_dist_ = 1.0
            self.prev_x_ = self.x_
            self.prev_y_ = self.y_
            diff_angle = self.theta_ - self.prev_theta_
            diff_angle = (diff_angle + math.pi) % (2 * math.pi) - math.pi
            self.goal_angle_ -= diff_angle
            self.prev_theta_ = self.theta_
            self.linear_vel_ = 0.0

            # Are we there yet
            if abs(self.goal_angle_) <= 1e-3:
                self.vel_pub_.publish(self.stop_)
                self.flipper_ = False
                self.get_logger().info("Rotation complete")
                return

            # Keep going
            msg = Twist()
            target = min(1.0, max(self.goal_angle_, -1.0))
            self.angular_vel_ += self.alpha_ * (target - self.angular_vel_)
            msg.angular.z = self.angular_vel_
            self.vel_pub_.publish(msg)


    # Fuck my life
    def path_calc(self, angle):
        # Wait for odom
        if self.x_ is None or self.y_ is None or self.theta_ is None:
            return

        # Iterate through the path
        self.path_ = [[self.x_, self.y_, self.theta_]]
        for i in range(self.mode_+3):
            target_angle = self.theta_ + i * angle
            start_x, start_y, _ = self.path_[-1]
            for j in range(1, self.points_per_line_+1):
                dist = self.goal_dist_ / self.points_per_line_ * j
                self.path_.append([
                    start_x + dist * math.cos(target_angle),
                    start_y + dist * math.sin(target_angle),
                    target_angle])

        # Assign previous values
        self.prev_x_ = self.x_
        self.prev_y_ = self.y_
        self.prev_theta_ = self.theta_

        # Done
        self.path_calcd_ = True


    # Fuck my computer's life
    def error_brute_forcer(self):
        # Force closest point in polygon
        min_dist = math.inf
        for point in self.path_:
            dist = math.sqrt((point[0] - self.x_)**2 + (point[1] - self.y_)**2)
            if dist < min_dist:
                min_dist = dist

        # Publish my shitlist
        msg = Float32()
        msg.data = min_dist
        self.info_pub_.publish(msg)
        

    # The process
    def _process(self):
        # degubbung or some bs
        if not self.path_calcd_:
            self.path_calc(2*math.pi/(3+self.mode_))

        # Runnin'
        else:
            self.thingy(2*math.pi/(3+self.mode_))
            self.error_brute_forcer()



def main(args=None):
    rclpy.init(args=args)
    try:
        cmd_publisher = Nav4(sys.argv[1:])
        rclpy.spin(cmd_publisher)
    except KeyboardInterrupt:
        cmd_publisher.destroy_node()
        rclpy.shutdown()
    	
if __name__ == '__main__':
    main()