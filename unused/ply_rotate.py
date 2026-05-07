
import open3d as o3d
import numpy as np

# Load the mesh
# mesh = o3d.io.read_triangle_mesh("field/RMUC2025_National.PLY")
mesh = o3d.io.read_triangle_mesh("field/RMUC2026.ply")
print(f"Original mesh: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")

# Rotate step by step
center = mesh.get_center()

# Then apply pitch (-90° around Y)
mesh.rotate(mesh.get_rotation_matrix_from_xyz((0, np.deg2rad(90), 0)), 
            center=center)

# First apply yaw (90° around Z)
mesh.rotate(mesh.get_rotation_matrix_from_xyz((0, 0, np.deg2rad(90))), 
            center=center)

mesh.compute_vertex_normals()
o3d.io.write_triangle_mesh("field/RMUC2026_oriented.ply", mesh)
o3d.visualization.draw_geometries([mesh])
