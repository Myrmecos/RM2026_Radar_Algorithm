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
    1. in `params_2026.yaml`, change `K` and `dist_coeffs`
3. field positions
    1. in `params_2026.yaml`, change `mesh_path` and `keypoints`
    2. set `inference_video` to `false`
4. referee serial port: 
    1. change in `params.yaml`, change `port`
    

# Nvidia driver fail: simple solutions:
sudo dkms install -m nvidia -v 580.119.02

# Adapting the ply file to the code
1. unused/ply_downsample.py: downsample the ply file to fewer points
2. unused/ply_rotate: rotate ply model to correct orientation (shorter edge towards us)
3. unused/ply_resize: resize the ply model (originally in mm, now in m)

