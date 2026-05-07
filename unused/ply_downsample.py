import open3d as o3d

# Load the mesh
# mesh = o3d.io.read_triangle_mesh("field/RMUC2025_National.PLY")
mesh = o3d.io.read_triangle_mesh("field/RMUC2026_downsampled.ply")
print(f"Original mesh: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
o3d.visualization.draw_geometries([mesh])
mesh.remove_unreferenced_vertices()

# Make sure it has normals (important for some operations)
if not mesh.has_vertex_normals():
    mesh.compute_vertex_normals()

# Method 1: Quadric Error Metric Decimation (Best for preserving shape)
target_triangles = 3000

mesh_simplified = mesh.simplify_quadric_decimation(
    target_number_of_triangles=target_triangles,
    # You can tune these if needed:
    # maximum_error=inf,      # default: no limit
    # boundary_weight=1.0     # higher = preserve boundaries more
)

print(f"Simplified mesh: {len(mesh_simplified.vertices)} vertices, "
      f"{len(mesh_simplified.triangles)} triangles")

# Save the result
o3d.io.write_triangle_mesh("field/RMUC2026_downsampled_1.ply", mesh_simplified)

# Optional: Visualize
o3d.visualization.draw_geometries([mesh_simplified])