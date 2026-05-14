# import only code from the workspace.

import numpy as np
import cv2
import yaml
import matplotlib.pyplot as plt

# 1. use plt to show the image, and takes a click's selected point
img_path = "field/RMUC2026.jpg" # radar  station's perspective
bev_path = "field/RMUC2026.png" # bird's eye view

img_path = "/home/etmphile/桌面/RM2025-Radar-Algorithm/videos/first_frame.png"
bev_path = "field/field_image.png"

# Load config for camera intrinsics
with open("config/params.yaml", "r") as f:
    config = yaml.safe_load(f)

K = np.array(config["transform"]["K"], dtype=np.float64)
dist_coeffs = np.array(config["transform"]["dist_coeffs"], dtype=np.float64)

# 2. use the R and t and code from workspace to project the selected point onto the 3d scene
# output the 3d position
# Future: use point select-extrinsic calib code from the project to get R and t

# calibrated R
# R = np.array([[0.9811, -0.1676, 0.0964],
#     [-0.1771, -0.9791, 0.1001],
#     [0.0776, -0.1153, -0.9903]], dtype=np.float64)
# t = np.array([[-0.6277], [1.4039], [17.2972]], dtype=np.float64)

# # original R
R = [[0.99530147, -0.03039188, -0.09193101],
        [-0.01339114, -0.98354371, 0.18017339],
        [-0.09589397, -0.17809578, -0.97932948],]
t = [[-0.68605672], [1.13893625], [15.32698638]]
R = np.array(R)
t = np.array(t)

# Import PixelToWorld from workspace
import sys
sys.path.insert(0, "/home/etmphile/桌面/RM2025-Radar-Algorithm")
from transform.ray_renderer import PixelToWorld
import open3d as o3d

# Build converter
# mesh = o3d.io.read_triangle_mesh("field/RMUC2026_oriented_scaled.ply")
mesh = o3d.io.read_triangle_mesh("field/RMUC2025_Regional.PLY")
converter = PixelToWorld(K, R, t, mesh, dist_coeffs)

# Load images
img = cv2.imread(img_path)
bev = cv2.imread(bev_path)
bev = cv2.rotate(bev, cv2.ROTATE_180)

# Click handler
clicked_points_img = []
clicked_points_bev = []

def on_click(event):
    if event.button == 1 and event.xdata is not None and event.ydata is not None:
        u, v = event.xdata, event.ydata
        pixel = (u, v)
        world_3d = converter.pixel_to_world(pixel)
        print(f"Pixel ({u:.1f}, {v:.1f}) -> 3D: {world_3d}")

        if world_3d is not None:
            # Project to ground plane (z=0)
            # Ray: origin + t * world_dir, solve for t when z=0
            # origin = -R.T @ t.flatten()
            # cam_dir = np.linalg.inv(K) @ np.array([u, v, 1.0])
            # world_dir = R.T @ cam_dir
            # world_dir = world_dir / np.linalg.norm(world_dir)
            ground_point = [world_3d[0]+7.5, world_3d[2]+14]

            # Find t where z=0
            if True:
                # Map to BEV image
                # Field is 16m x 12m, BEV is 768x448

                # Center offset: field center at (8, 6)
                bev_u = (ground_point[0])/15
                bev_v = (ground_point[1])/28

                print("BEV x:", bev_u)
                print("BEF y:", bev_v)

                bev_u *= bev.shape[0]
                bev_v *= bev.shape[1]

                bev_u, bev_v = bev_v, bev_u

                # Draw on BEV

                clicked_points_img.append((u, v))
                clicked_points_bev.append((bev_u, bev_v))

                # Update BEV subplot with all clicked points
                ax2.clear()
                ax2.set_title("Bird's Eye View - Green dots = selected points")
                ax2.imshow(cv2.cvtColor(bev, cv2.COLOR_BGR2RGB))
                for pt in clicked_points_bev:
                    ax2.plot(pt[0], pt[1], 'go', markersize=10)
                fig.canvas.draw_idle()

                # Update original image subplot with all clicked points
                ax1.clear()
                ax1.set_title("Radar View - Click to select point")
                ax1.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                for pt in clicked_points_img:
                    ax1.plot(pt[0], pt[1], 'ro', markersize=5)
                fig.canvas.draw_idle()

# Show images
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
ax1.set_title("Radar View - Click to select point")
ax1.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
ax1.set_xlabel("Click a point")
fig.canvas.mpl_connect('button_press_event', on_click)

ax2.set_title("Bird's Eye View - Green dots = selected points")
ax2.imshow(cv2.cvtColor(bev, cv2.COLOR_BGR2RGB))

plt.tight_layout()
plt.show()

print("Debug projection complete.")
