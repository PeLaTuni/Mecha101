import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import sys
import math


class Nav3(Node):
    def __init__(self, args):
        super().__init__("nav3")

        # Misc
        self.sleepy_ = self.create_rate(2.0)
        self.stop_ = Twist()
        self.stop_.linear.x = 0.0
        self.stop_.angular.z = 0.0

        # Goal
        self.goal_x_ = float(args[0])
        self.goal_y_ = float(args[1])
        self.goal_theta_ = float(args[2])

        # Position
        self.x_ = 0.0
        self.y_ = 0.0
        self.theta_ = 0.0

        # Flags
        self.reached_ = False
        self.goal_ = False

        # Subscribe to odom, because that is good
        self.create_subscription(Odometry, "/odom", self.odom_callback, 1)

        # Publish to /cmd_vel
        self.vel_pub_ = self.create_publisher(Twist, "/cmd_vel", 1)

        # Spin my head right round right round
        self.create_timer(0.1, self._process)


    # Callbacks
    def odom_callback(self, msg):
        self.x_ = msg.pose.pose.position.x
        self.y_ = msg.pose.pose.position.y
        z = msg.pose.pose.orientation.z
        w = msg.pose.pose.orientation.w
        self.theta_ = 2*math.atan2(z, w)


    # The process
    def _process(self):            
        if not self.reached_:
            # I despise efficiency
            diff_x = self.goal_x_ - self.x_
            diff_y = self.goal_y_ - self.y_
            diff_angle = math.atan2(diff_y, diff_x)
            dist = math.sqrt((self.goal_x_ - self.x_)**2 + (self.goal_y_ - self.y_)**2)

            # Angluar
            angle_error = diff_angle - self.theta_
            angle_error = (angle_error + math.pi) % (2 * math.pi) - math.pi

            # Check if leave
            if dist <= 1e-2:
                self.reached_ = True
                self.vel_pub_.publish(self.stop_)
                self.get_logger().info("Reached")
                return

            # Keep going if not
            msg = Twist()
            msg.linear.x = min(1.0, max(dist, -1.0))
            msg.angular.z = min(1.0, max(angle_error, -1.0))
            self.vel_pub_.publish(msg)

        elif not self.goal_:
            # Calculate correct angle
            angle_error = self.goal_theta_ - self.theta_
            angle_error = (angle_error + math.pi) % (2 * math.pi) - math.pi

            # Exit if good
            if abs(angle_error) <= 1e-3:
                self.goal_ = True
                self.vel_pub_.publish(self.stop_)
                self.get_logger().info("Done :)")
                return

            # Keep spinning
            msg = Twist()
            msg.angular.z = min(1.0, max(angle_error, -1.0))
            self.vel_pub_.publish(msg)



def main(args=None):
    rclpy.init(args=args)
    try:
        cmd_publisher = Nav3(sys.argv[1:])
        rclpy.spin(cmd_publisher)
    except KeyboardInterrupt:
        cmd_publisher.stop_turtlebot()
        cmd_publisher.destroy_node()
        rclpy.shutdown()
    	
if __name__ == '__main__':
    main()