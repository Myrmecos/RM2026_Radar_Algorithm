#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROS2 camera publisher for RM2025-Radar-Algorithm.
Publishes RGB images to the topic /rgb_image.

Usage examples:
  python cam_publisher.py --camera_driver mock --video_source 0
  python cam_publisher.py --camera_driver mock --video_source video.mp4
  python cam_publisher.py --camera_driver hik --device_config config/device.yaml
"""

import argparse
import sys
from types import SimpleNamespace

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

try:
    from cv_bridge import CvBridge
    _HAS_CV_BRIDGE = True
except ImportError:
    _HAS_CV_BRIDGE = False


def parse_args():
    parser = argparse.ArgumentParser(description="Publish camera images to /rgb_image")
    parser.add_argument(
        "--camera_driver",
        choices=["mock", "hik"],
        default="hik",
        help="Camera backend: hikrobot driver by default, or mock webcam/video for testing",
    )
    parser.add_argument(
        "--video_source",
        default="0",
        help="Video source for mock driver: camera index or video file path",
    )
    parser.add_argument(
        "--device_config",
        default="config/device.yaml",
        help="Device YAML config used by the Hik camera driver",
    )
    parser.add_argument(
        "--topic",
        default="/rgb_image",
        help="ROS2 topic name to publish the RGB image on",
    )
    parser.add_argument(
        "--publish_rate",
        type=float,
        default=10.0,
        help="Publishing rate in Hz",
    )
    parser.add_argument(
        "--capture_width",
        type=int,
        default=0,
        help="Mock camera capture width (0 = keep default)",
    )
    parser.add_argument(
        "--capture_height",
        type=int,
        default=0,
        help="Mock camera capture height (0 = keep default)",
    )
    parser.add_argument(
        "--group_id",
        default="publisher",
        help="Image group id for camera ring buffer",
    )
    return parser.parse_args()


def load_yaml_config(path: str) -> dict:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_hik_args(device_config_path: str) -> SimpleNamespace:
    cfg = load_yaml_config(device_config_path)
    camera_cfg = cfg.get("camera", {})
    return SimpleNamespace(
        width=int(camera_cfg.get("width", 5472)),
        height=int(camera_cfg.get("height", 3648)),
        exposure_time=float(camera_cfg.get("exposure_time", 10000.0)),
        gain=float(camera_cfg.get("gain", 23.0)),
        acquisition_rate=float(camera_cfg.get("acquisition_rate", 19.0)),
        display_fps=bool(camera_cfg.get("display_fps", True)),
        recording_workers_num=int(camera_cfg.get("recording_workers_num", 2)),
        recording_save_root_dir=str(
            camera_cfg.get("recording_save_root_dir", "saved_images")
        ),
    )


class CameraPublisher(Node):
    def __init__(self, camera, topic: str, publish_rate: float, group_id: str):
        super().__init__("cam_publisher")
        self.camera = camera
        self.topic = topic
        self.group_id = group_id
        self.publisher = self.create_publisher(Image, topic, 10)
        self.bridge = CvBridge() if _HAS_CV_BRIDGE else None
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_image)
        self.get_logger().info(f"Publishing RGB images to {topic} at {publish_rate} Hz")

    def publish_image(self):
        image, timestamp = self.camera.get_image_latest(self.group_id, timeout=1.0)
        if image is None:
            self.get_logger().warning("No image received from camera")
            return

        try:
            msg = self._to_image_message(image)
        except Exception as exc:
            self.get_logger().error(f"Failed to convert image to ROS msg: {exc}")
            return

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera"
        self.publisher.publish(msg)
        self.get_logger().debug("Published /rgb_image frame")

    def _to_image_message(self, image: np.ndarray) -> Image:
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("Image must be HxWx3 RGB numpy array")

        if self.bridge is not None:
            try:
                return self.bridge.cv2_to_imgmsg(image, encoding="rgb8")
            except Exception as exc:
                self.get_logger().warning(
                    f"cv_bridge conversion failed, falling back to manual Image msg: {exc}"
                )
                self.bridge = None

        msg = Image()
        msg.height = int(image.shape[0])
        msg.width = int(image.shape[1])
        msg.encoding = "rgb8"
        msg.is_bigendian = 0
        msg.step = int(image.shape[1] * 3)
        msg.data = image.tobytes()
        return msg


def make_mock_camera(video_source: str, capture_width: int = 0, capture_height: int = 0):
    from driver.hik_camera.mock_hik import SimpleHikCamera

    try:
        source = int(video_source)
    except ValueError:
        source = video_source

    camera = SimpleHikCamera(source, width=capture_width, height=capture_height)
    camera.register_group("publisher")
    return camera


def make_hik_camera(device_config: str):
    from driver.hik_camera.hik import SimpleHikCamera

    args = build_hik_args(device_config)
    camera = SimpleHikCamera(args)
    camera.register_group("publisher")
    camera.start_streaming()
    return camera


def main():
    args = parse_args()
    rclpy.init()

    try:
        if args.camera_driver == "mock":
            camera = make_mock_camera(
                args.video_source,
                capture_width=args.capture_width,
                capture_height=args.capture_height,
            )
        else:
            camera = make_hik_camera(args.device_config)

        node = CameraPublisher(
            camera=camera,
            topic=args.topic,
            publish_rate=args.publish_rate,
            group_id=args.group_id,
        )
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass
    finally:
        try:
            if hasattr(camera, "stop_streaming"):
                camera.stop_streaming()
        except Exception:
            pass
        rclpy.shutdown()


if __name__ == "__main__":
    main()
