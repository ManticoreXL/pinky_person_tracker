import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'pinky_person_tracker'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ManticoreXL',
    maintainer_email='zip3366@naver.com',
    description='Pinky Pro YOLO Person Tracker',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'tracker_node = pinky_person_tracker.tracker_node:main',
            'camera_node = pinky_person_tracker.camera_node:main'
        ],
    },
)