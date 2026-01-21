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
1. python main.py --config config/params.yaml --device_config config/device.yaml
2. mark keypoints: demo/demo1.png

# todo
1. communication with referee
2. training better car detection