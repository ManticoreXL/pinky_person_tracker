from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pinky_person_tracker',
            executable='tracker_node',
            name='pinky_tracker_node',
            output='screen'
        )
    ])