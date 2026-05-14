# Pinky Person Tracker
Pinky Pro 로봇을 위한 카메라 기반 사람 인식 및 자율 추적 ROS 2 패키지입니다. Ultralytics YOLOv8 모델을 사용하여 실시간으로 사람을 감지하고, 유한 상태 기계(FSM)를 통해 로봇의 주행, 전면 디스플레이(표정), 후면 LED를 통합적으로 제어합니다.

## 시연 영상
[![Pinky Pro 시연 영상](https://img.youtube.com/vi/p42ta32EBGg/maxresdefault.jpg)](https://youtu.be/p42ta32EBGg)

## 시스템 아키텍처
이 패키지는 연산 부하를 분산하기 위해 로봇 측과 호스트 PC 측으로 나뉘어 동작하도록 설계되었습니다.
- 로봇 측: Picamera2를 이용해 영상을 수집하고 ROS 2 이미지 토픽으로 발행하며, 디스플레이 및 LED 제어 서비스 서버를 구동합니다.
- 호스트 PC 측: 무거운 YOLO 연산과 FSM 기반의 트래킹 제어 로직을 수행하여 로봇으로 주행 명령(Twist)과 상태 변경 서비스 요청을 전송합니다.

## FSM (유한 상태 기계) 로직
로봇은 카메라에 인식된 사람의 유무에 따라 다음 3가지 상태로 유기적으로 동작합니다.

1. IDLE (대기 상태)
- 동작: 지정된 속도로 제자리에서 천천히 회전하며 주변을 살핍니다.
- 시각 피드백: 핑크색 LED 점등, 랜덤 표정 출력 (bored, basic, interest)
- 전이 조건: 사람이 감지되면 TRACK 상태로 변경

2. TRACK (추적 상태)
- 동작: 사람의 중심 좌표를 계산하여 카메라 정중앙에 위치하도록 로봇이 회전하며 추적합니다.
- 시각 피드백: 초록색 LED 점멸 (0.5초 간격), 랜덤 표정 출력 (happy, fun)
- 전이 조건: 사람을 화면에서 놓치고 0.5초가 경과하면 SEARCH 상태로 변경

3. SEARCH (탐색 상태)
- 동작: 사람을 잃어버린 시점을 기준으로 10초 동안 좌우 부채꼴 범위로 스윕(Sweep)하며 주변을 재탐색합니다.
- 시각 피드백: 푸른색 LED 점멸 (1.0초 간격), 슬픈 표정 출력 (sad)
- 전이 조건: 10초 이내에 사람을 다시 찾으면 TRACK 상태로 복귀, 10초가 지나도 찾지 못하면 IDLE 상태로 복귀

## 의존성 패키지 (Dependencies)
- ROS 2 (Ubuntu 24.04 LTS 환경 권장)
- Python 3.12+
- Ultralytics (YOLO)
- OpenCV (cv_bridge)
- Picamera2
- Pinky Pro Base Packages

## 설치 및 빌드 방법 (Installation)

로봇과 호스트 PC 양쪽 모두 동일한 워크스페이스 구조에 패키지를 클론하고 빌드해야 합니다.

1. 리포지토리 클론
```
cd ~/pinky/src
git clone https://github.com/ManticoreXL/pinky_person_tracker.git
```

2. 파이썬 라이브러리 설치 (호스트 PC 전용)
YOLO 구동을 위해 호스트 PC의 환경에 맞게 Ultralytics를 설치합니다. (가상환경 사용을 적극 권장합니다.)
```
python3 -m pip install ultralytics
```

3. 워크스페이스 빌드
```
cd ~/pinky
colcon build --symlink-install --packages-select pinky_person_tracker
source install/setup.bash
```

## 실행 방법 (Usage)

1. 로봇(Pinky Pro) 측 실행
라이다, 모터 등 로봇의 기본 구동 패키지를 실행한 후, 본 패키지의 로봇 런치 파일을 실행합니다.
```
ros2 launch pinky_bringup bringup.launch.py
```
```
ros2 launch pinky_person_tracker robot.launch.py
```

2. 호스트 PC 측 실행
로봇과 동일한 네트워크에 연결된 상태에서 추적 노드를 실행합니다.
```
ros2 launch pinky_person_tracker host.launch.py
```

## 동적 파라미터 (Parameters)
IDLE 상태에서의 제자리 회전 속도는 노드 실행 중에도 파라미터를 통해 실시간으로 변경할 수 있습니다.
- 파라미터 이름: idle_spin_speed
- 기본값: -0.1204 (rad/s)

변경 명령어 예시:
```
ros2 param set /pinky_tracker_node idle_spin_speed -0.15
```