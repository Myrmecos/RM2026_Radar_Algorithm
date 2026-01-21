from ultralytics import YOLO

# load a model
model = YOLO("yolov8n.pt")  # load an official model

# train the model
model.train(cfg="config/armor_training_config.yaml", epochs=20, imgsz=192, batch=16)