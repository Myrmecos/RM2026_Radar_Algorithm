
import yaml
import tkinter as tk
import matplotlib.pyplot as plt
import numpy as np
import cv2
import open3d as o3d

# load the settings
with open("config/params_project_test_lab.yaml", "r") as f:
    config = yaml.safe_load(f)

camera_matrix=np.array(config["transform"]["K"])
K = camera_matrix
R=np.array(config["transform"]["R"])
T=np.array(config["transform"]["t"])
dist_coeffs=np.array(config["transform"]["dist_coeffs"])
mesh_path = config['field']['mesh_path']


# TODO: visualize it (with specific camera matrix K, rotation matrix R, translation matrix t) and save it as an image (field/RMUC2026.jpg)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import pyrender
import os
import open3d as o3d

# 1. Determine Image Dimensions from K
width = int(K[0, 2] * 2)
height = int(K[1, 2] * 2)

# 2. Load Mesh using Open3D (more robust for PLY binary formats)
mesh_path = config["field"]["mesh_path"]
print("loading mesh:", mesh_path)
o3d_mesh = o3d.io.read_triangle_mesh(mesh_path)

# Convert Open3D mesh to Pyrender Mesh
# We extract vertices and triangles manually
vertices = np.asarray(o3d_mesh.vertices)
faces = np.asarray(o3d_mesh.triangles)

# Create a pyrender-compatible mesh
# If your mesh doesn't have colors, we'll give it a default gray
if not o3d_mesh.has_vertex_colors():
    o3d_mesh.paint_uniform_color([0.6, 0.6, 0.6])
colors = np.asarray(o3d_mesh.vertex_colors)

# Build the pyrender mesh
import trimesh
# We use trimesh as an intermediary container because pyrender likes it
tm_mesh = trimesh.Trimesh(vertices=vertices, faces=faces, vertex_colors=colors)
mesh = pyrender.Mesh.from_trimesh(tm_mesh)

# 3. Create Pyrender Scene
scene = pyrender.Scene(bg_color=[0.1, 0.1, 0.1])
scene.add(mesh)

# 4. Setup Camera with K (Intrinsics)
camera = pyrender.IntrinsicsCamera(
    fx=K[0, 0], fy=K[1, 1], cx=K[0, 2], cy=K[1, 2]
)

# 5. Setup Camera Pose (Extrinsics)
# Pose = [R.T | -R.T @ T]
pose = np.eye(4)
pose[:3, :3] = R.T
pose[:3, 3] = (-R.T @ T).flatten()

# OpenCV (Z-forward, Y-down) to OpenGL (Z-backward, Y-up) conversion
flip_yz = np.array([
    [1,  0,  0, 0],
    [0, -1,  0, 0],
    [0,  0, -1, 0],
    [0,  0,  0, 1]
])
pose = pose @ flip_yz

scene.add(camera, pose=pose)

# 6. Add Lighting (Headlamp style)
light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=4.0)
scene.add(light, pose=pose)

# 7. Render
r = pyrender.OffscreenRenderer(width, height)
img, _ = r.render(scene)

# 8. Save and Update Config
os.makedirs("field", exist_ok=True)
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
cv2.imwrite("field/RMUC2026.jpg", img_bgr)
config["transform"]["demo_img_path"] = "field/RMUC2026.jpg"

print(f"Projected mesh image saved to field/RMUC2026.jpg")
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
cv2.imwrite("field/RMUC2026.jpg", img)
print("Saved projected image to field/RMUC2026.jpg")


# TODO: allow clicking, and cast a ray to the clicked direction, report the first point encountered
from ray_renderer import PixelToWorld, PixelToWorldGUI

root = tk.Tk()
converter = PixelToWorld.build_from_config(config)
app = PixelToWorldGUI(root, config["transform"]["demo_img_path"], converter, scale_factor=0.5)
plt.ion()  # 开启Matplotlib交互模式
root.mainloop()