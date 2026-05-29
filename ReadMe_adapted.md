# 太长不看版
source ros_setup.bash

sudo chmod 766 /dev/ttyACM0 /dev/ttyACM1

python main.py --config config/params.yaml --device_config config/device.yaml

# Training
1. train car detector: python train/car_train.py
2. train armor detector: python train/armor_train.py
3. train digit classifier: python -m model.digit_classifier.train --dataset-path training_data/RM2025-Armor-Pattern-Public-Dataset/RM2025-Armor-Pattern-Dataset --batch-size 32

# Converting
1. what we need: 
    1. car_v1.5.engine
    2. armor_v0.7.engine
    3. MobileNet_v3.1.pth

2. what we have: 
    1. armor and car are both .pt
    2. mobilenet already .pth

# pyqt problem: core.py launch() hardcoded pyqt's path to the developer's home dir! Change it to yours

# run code: 
0. source ros_setup.bash
1. python main.py --config config/params.yaml --device_config config/device.yaml
2. mark keypoints: demo/demo1.png
3. specify own 3d keypoints in argument

# use camera or video? see:
params.yaml, debug, inference_video.

# calibration
go to ~/ros_ws/

# What to chagne to adapt to new environment 
1. image visualization
    1. in core.py, change: `self.field_image = cv2.imread("./field/RMUC2026.png")`
    2. lower-right is (0, 0); upper left is (1500, 2800)
2. camera intrinsic
    1. in `params.yaml`, change `K` and `dist_coeffs`
3. field model
    1. change `params.yaml`'s mesh path to your model, e.g. `field/RMUC2026.ply`
    2. change the calib points `transform/keypoint_6.txt`. This part is hardcoded and yaml file is of no use.
4. Inference mode
    2. set `inference_video` to `false`
5. referee serial port: 
    1. change in `params.yaml`, change `port`
    

# Nvidia driver fail: simple solutions:
sudo dkms install -m nvidia -v 580.119.02

# Adapting the ply file to the code
1. unused/ply_downsample.py: downsample the ply file to fewer points
2. unused/ply_rotate: rotate ply model to correct orientation (shorter edge towards us)
3. unused/ply_resize: resize the ply model (originally in mm, now in m)


# testing communication
1. sudo socat -d -d PTY,link=/dev/ttyV0,raw,echo=0 PTY,link=/dev/ttyV1,raw,echo=0

# Remove the need for chmod every time
1. sudo visudo -f /etc/sudoers.d/astar-nopasswd
2. astar ALL=(ALL) NOPASSWD: ALL
3. save
4. how to remove: delete file in step 1.


#
1. model/armor_detector.pt: determine if we are using horizon's or hkust's model

# testing communication
sudo socat -d -d PTY,link=/dev/ttyV0,raw,echo=0 PTY,link=/dev/ttyV1,raw,echo=0
sudo chmod 666 /dev/ttyV0 /dev/ttyV1
python test_comm/sim_radar_referee.py --mode referee --referee-port /dev/ttyV1

change the reference: port in params.yaml to '/dev/ttyV0'


# 复盘
1. ffmpeg -framerate 30 -pattern_type glob -i 'ssd/referee_logs/saved_images_2026-05-28_15:28:11.729/*.jpg' -c:v libx264 -pix_fmt yuv420p -crf 23 "ssd/referee_logs/saved_images_2026-05-28_15:28:11.729.mp4"

0. 入场前保证
    1. 线解缠绕
    2. 光圈合理
1. 进场快速部署：
    1. 电脑插电源
    2. 插裁判系统
    3. bash start.sh
    3. 放好相机，拉线
    4. 标定

2. 现在检查：
    1. 使用地图文件是否正确
        是对的，只要写入params.yaml即可。
    2. 标定用点重设置（选择不容易遮挡的点）
        设置了，在demo4.png
    3. 测试标定用新点准确率 
        模拟数据图像上是准的
        真实图像呢：
    4. 压力测试：相机前面提供视频
        3小时空白场景不产生问题（似乎）
    5. 重新标定相机
    
3. 留意：
    1. 如何触发相机报错和检测缺失
        1. 连接松弛，晃动导致部分图像不完整
        2. 若不拔插就重新插紧，会导致该问题（报错Get frame failed! Error code: 0x80000003）持续出现。
        3. 解决方法是确保相机线两头都插紧。若出现问题，拔插（不是仅仅插紧）

4. 标定
    1. in one terminal: python cam_publisher.py 
    2. in another terminal, run: ros2 run camera_calibration cameracalibrator --size 10x7 --square 0.020 image:=/rgb_image

    0. ros2 run camera_calibration cameracalibrator --size 10x7 --square 0.020 image:=/rgb_image