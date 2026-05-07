import open3d as o3d

# Load the mesh
mesh = o3d.io.read_triangle_mesh("field/RMUC2026_downsampled.ply")
print(f"Original mesh: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")

# Print original size
print("\n=== Before Scaling ===")
print("Min bounds:", mesh.get_min_bound())
print("Max bounds:", mesh.get_max_bound())
print("Center:", mesh.get_center())
print("Extent (size):", mesh.get_max_bound() - mesh.get_min_bound())

# === Scale to 1/1000 ===
scale_factor = 0.001
mesh.scale(scale_factor, center=[0,0,0])

# Optional: Recompute normals after scaling
mesh.compute_vertex_normals()

print("\n=== After Scaling (1/1000) ===")
print("Min bounds:", mesh.get_min_bound())
print("Max bounds:", mesh.get_max_bound())
print("Extent (size):", mesh.get_max_bound() - mesh.get_min_bound())

# Save the scaled mesh
o3d.io.write_triangle_mesh("field/RMUC2026_oriented_scaled.ply", mesh, write_vertex_colors=True)
print("\nSaved as: field/RMUC2026_oriented_scaled.ply")