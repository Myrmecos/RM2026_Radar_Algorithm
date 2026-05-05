import open3d as o3d

# Load the mesh
mesh = o3d.io.read_triangle_mesh("field/RMUC2026_downsampled.ply")
print(f"Original mesh: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")

# Optional: repair common issues
mesh = mesh.remove_duplicated_vertices()
mesh = mesh.remove_duplicated_triangles()
mesh = mesh.remove_degenerate_triangles()

# Global simplification (uniform)
target_triangles = 3000   # Adjust based on your needs (e.g. 20k ~ 100k)
simplified = mesh.simplify_quadric_decimation(
    target_number_of_triangles=target_triangles,
    maximum_error=0.1,      # maximum allowed error (in world units)
    boundary_weight=1.0      # higher = preserve boundaries better
)

print(f"Simplified mesh: {len(simplified.vertices)} vertices, {len(simplified.triangles)} triangles")

# Save
o3d.io.write_triangle_mesh("field/RMUC2025_downsampled1.ply", simplified, write_ascii=False, compressed=True)


# import pymeshlab

# ms = pymeshlab.MeshSet()
# ms.load_new_mesh("field/RMUC2026.ply")

# # Quadric Edge Collapse
# ms.meshing_decimation_quadric_edge_collapse(
#     targetfacenum=3000,           # desired number of faces
#     preservetopology=True,
#     preservenormal=True,
#     qualityweight=1.0
# )

# ms.save_current_mesh("field/RMUC2026_downsampled.ply")