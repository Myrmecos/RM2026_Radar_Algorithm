import open3d as o3d

# Load your mesh
mesh = o3d.io.read_triangle_mesh("field/RMUC2026_oriented_scaled.ply")
# mesh = o3d.io.read_triangle_mesh("field/RMUC2025_Regional.PLY")
print(f"Original mesh: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")

# Create a coordinate frame (world origin)
coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
    size=5.0,      # Adjust size according to your mesh scale (important!)
    origin=[0, 0, 0]
)

# Optional: Make mesh nicer for visualization
if not mesh.has_vertex_colors():
    mesh.paint_uniform_color([0.7, 0.7, 0.7])

o3d.visualization.draw_geometries([mesh])

mesh.compute_vertex_normals()

# Visualize mesh + coordinate frame
o3d.visualization.draw_geometries(
    [mesh, coord_frame],
    window_name="Mesh with World Coordinate Frame",
    width=1280,
    height=720,
    mesh_show_back_face=True
)