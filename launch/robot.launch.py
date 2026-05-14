from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 디스플레이(표정) 서버 노드 (pinky_pro 패키지)
        Node(
            package='pinky_emotion',
            executable='emotion_server', 
            name='pinky_emotion',
            output='screen'
        ),
        # LED 서버 노드 (pinky_pro 패키지)
        Node(
            package='pinky_led',
            executable='led_server', 
            name='led_service_server',
            output='screen'
        ),
        # 카메라 퍼블리셔 노드 (사용자 커스텀 패키지)
        Node(
            package='pinky_person_tracker',
            executable='camera_node',
            name='camera_publisher',
            output='screen'
        )
    ])