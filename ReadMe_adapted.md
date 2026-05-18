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
3. specify own 3d keypoints: hardcoded, in transform/keypoint_6.txt. The name specified in yaml file does not count, as the keypoint_6.txt is hardcoded.

# use camera or video? see:
params.yaml, debug, inference_video.

# todo
1. communication with referee
2. training better car detection

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