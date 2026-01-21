from ultralytics import YOLO

# load a model
model = YOLO("yolov8n.pt")  # load an official model

# train the model
model.train(cfg="config/car_training_config.yaml", data = "/home/etmphile/桌面/RM2025-Radar-Algorithm/training_data/RM2025-Car-Public-Dataset/config/config.yaml", epochs=20, imgsz=192, batch=16)