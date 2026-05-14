import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import time
import math
import random
from enum import Enum

# Pinky 서비스 인터페이스 임포트
from pinky_interfaces.srv import Emotion, SetLed
from ultralytics import YOLO

class State(Enum):
    IDLE = 1
    TRACK = 2
    SEARCH = 3

class PinkyTrackerNode(Node):
    def __init__(self):
        super().__init__('pinky_tracker_node')
        
        # 1. 파라미터 선언: IDLE 상태의 회전 속도 (기본값: 기존 대비 약 15% 증가)
        self.declare_parameter('idle_spin_speed', -0.1204)
        
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.image_sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        
        self.emotion_client = self.create_client(Emotion, 'set_emotion')
        self.led_client = self.create_client(SetLed, 'set_led')
        
        self.bridge = CvBridge()
        self.yolo_model = YOLO('yolov8n.pt')
        
        self.current_state = State.IDLE
        self.person_detected = False
        self.person_center_x = 0
        self.image_width = 320 
        
        self.search_start_time = 0.0
        self.last_detection_time = time.time()
        
        self.led_blink_state = False
        self.last_blink_time = time.time()
        
        self.control_timer = self.create_timer(0.1, self.control_loop)
        
        self.enter_state(State.IDLE)
        self.get_logger().info('Tracker Node Started. Waiting for images...')

    def request_emotion(self, emo_str):
        if not self.emotion_client.wait_for_service(timeout_sec=1.0):
            return
        req = Emotion.Request()
        req.emotion = emo_str
        self.emotion_client.call_async(req)

    def request_led(self, command, r=0, g=0, b=0):
        if not self.led_client.wait_for_service(timeout_sec=1.0):
            return
        req = SetLed.Request()
        req.command = command
        req.r = int(r)
        req.g = int(g)
        req.b = int(b)
        self.led_client.call_async(req)

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.image_width = cv_image.shape[1]
        except Exception as e:
            return

        results = self.yolo_model(cv_image, classes=[0], verbose=False)
        person_found = False
        largest_area = 0
        
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                area = (x2 - x1) * (y2 - y1)
                if area > largest_area:
                    largest_area = area
                    self.person_center_x = int((x1 + x2) / 2)
                    person_found = True

        self.person_detected = person_found
        if person_found:
            self.last_detection_time = time.time()

        annotated_frame = results[0].plot()
        cv2.imshow("YOLO Tracker", annotated_frame)
        cv2.waitKey(1)

    def enter_state(self, new_state):
        self.current_state = new_state
        
        if self.current_state == State.IDLE:
            self.get_logger().info('State: IDLE')
            # 2. 표정 랜덤 선택 및 핑크색 LED 점등 (점멸 안함)
            selected_emo = random.choice(['bored', 'basic', 'interest'])
            self.request_emotion(selected_emo)
            self.request_led('fill', r=239, g=52, b=237) 
            
        elif self.current_state == State.TRACK:
            self.get_logger().info('State: TRACK')
            # 2. 표정 랜덤 선택 및 초록색 LED 점멸 시작
            selected_emo = random.choice(['happy', 'fun'])
            self.request_emotion(selected_emo)
            self.led_blink_state = True
            self.last_blink_time = time.time()
            self.request_led('fill', r=0, g=255, b=0)
            
        elif self.current_state == State.SEARCH:
            self.get_logger().info('State: SEARCH')
            # 2. Sad 표정 및 푸른색 LED 점멸 시작
            self.request_emotion('sad')
            self.led_blink_state = True
            self.last_blink_time = time.time()
            self.request_led('fill', r=0, g=0, b=255)
            self.search_start_time = time.time()

    def control_loop(self):
        twist_msg = Twist()
        current_time = time.time()
        
        if self.current_state == State.IDLE:
            if self.person_detected:
                self.enter_state(State.TRACK)
                return
            # 3. 파라미터로 설정된 속도 적용
            spin_speed = self.get_parameter('idle_spin_speed').get_parameter_value().double_value
            twist_msg.angular.z = spin_speed
            
        elif self.current_state == State.TRACK:
            if not self.person_detected and (current_time - self.last_detection_time > 0.5):
                self.enter_state(State.SEARCH)
                return
                
            # 2. 중간 속도(0.5초 간격) 초록색 LED 점멸 로직
            if current_time - self.last_blink_time > 0.5:
                self.led_blink_state = not self.led_blink_state
                self.last_blink_time = current_time
                if self.led_blink_state:
                    self.request_led('fill', r=0, g=255, b=0)
                else:
                    self.request_led('clear')

            error_x = (self.image_width / 2) - self.person_center_x
            p_gain = 0.005 
            twist_msg.angular.z = error_x * p_gain
            
        elif self.current_state == State.SEARCH:
            if self.person_detected:
                self.enter_state(State.TRACK)
                return
                
            elapsed_time = current_time - self.search_start_time
            if elapsed_time > 10.0:
                self.enter_state(State.IDLE)
                return
                
            # 2. 느린 속도(1.0초 간격) 푸른색 LED 점멸 로직
            if current_time - self.last_blink_time > 1.0:
                self.led_blink_state = not self.led_blink_state
                self.last_blink_time = current_time
                if self.led_blink_state:
                    self.request_led('fill', r=0, g=0, b=255)
                else:
                    self.request_led('clear')
                
            twist_msg.angular.z = 0.5 * math.sin(elapsed_time * 1.2) 

        self.cmd_pub.publish(twist_msg)

def main(args=None):
    rclpy.init(args=args)
    node = PinkyTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()