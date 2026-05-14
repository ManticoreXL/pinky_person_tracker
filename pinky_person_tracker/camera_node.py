import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from picamera2 import Picamera2
from libcamera import Transform

class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        self.publisher_ = self.create_publisher(Image, '/camera/image_raw', 10)
        self.bridge = CvBridge()
        
        self.picam2 = Picamera2()
        video_config = self.picam2.create_video_configuration(
            main={"size": (320, 240)}, 
            transform=Transform(hflip=True, vflip=True)
        )
        self.picam2.configure(video_config)
        self.picam2.start()
        
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info('Camera Publisher Started.')

    def timer_callback(self):
        try:
            frame_data = self.picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame_data, cv2.COLOR_RGB2BGR)
            msg = self.bridge.cv2_to_imgmsg(frame_bgr, encoding="bgr8")
            self.publisher_.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Camera capture error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.picam2.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()