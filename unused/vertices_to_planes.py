import open3d as o3d
import numpy as np

# Load point cloud
pcd = o3d.io.read_point_cloud("field/lab_0505.ply")

# === MINIMAL BUT IMPORTANT ADDITIONS ===
pcd = pcd.voxel_down_sample(voxel_size=0.06)        # <-- helps a lot for flatter look
print(f"Points after downsampling: {len(pcd.points)}")

# Statistical outlier removal
# pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
# Radius outlier removal
# pcd, _ = pcd.remove_radius_outlier(nb_points=16, radius=0.5)

o3d.visualization.draw_geometries([pcd])

pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
pcd.orient_normals_consistent_tangent_plane(k=20)

# Estimate normals (important for many methods)
pcd.estimate_normals()

# Option 1: Ball Pivoting (good for dense, uniform clouds)
distances = pcd.compute_nearest_neighbor_distance()
avg_dist = np.mean(distances)
radii = [avg_dist * r for r in [1, 2, 4]]

# Option 2: Poisson (excellent for closed surfaces)
mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    pcd, depth=7)          # <-- changed from 9 to 7 (flatter, fewer triangles)

# === Minimal post-processing for flatter result ===
densities = np.asarray(densities)
mesh.remove_vertices_by_mask(densities < np.quantile(densities, 0.05))

mesh = mesh.filter_smooth_taubin(number_of_iterations=5)           # <-- flatten
mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=15000)  # <-- fewer triangles

o3d.io.write_triangle_mesh("field/output_lab0505.ply", mesh)
o3d.visualization.draw_geometries([mesh])