import numpy as np
import pyvista as pv
import math




def get_calibration_icosahedron():

    phi = (1 + np.sqrt(5)) / 2
    a, b = 1, phi
    vertices = np.array([
        [-a, b, 0], [a, b, 0], [-a, -b, 0], [a, -b, 0],
        [0, -a, b], [0, a, b], [0, -a, -b], [0, a, -b],
        [b, 0, -a], [b, 0, a], [-b, 0, -a], [-b, 0, a]
    ])

    scale = 5 / np.linalg.norm(vertices[0])
    vertices *= scale

    faces = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ])
    return vertices, faces




def custom_calculate_face_normal(face_vertices):
    """
    Compute the face normal from 3 vertices using the cross product.
    Normalizes the resulting vector.
    """
    v1, v2, v3 = face_vertices
    edge1 = v2 - v1
    edge2 = v3 - v1
    normal = np.cross(edge1, edge2)
    normal /= np.linalg.norm(normal)
    return normal


# -------------------------------
# Comparison and Visualization using PyVista
# -------------------------------

def compare_normals():
    # Get calibration icosahedron (vertices and faces)
    vertices, faces = get_calibration_icosahedron()

    # Convert 'faces' into the flat format needed by PyVista.
    # For each face, prepend the number of vertices (here 3 since all faces are triangles).
    faces_flat = np.hstack([[3] + face.tolist() for face in faces]).astype(np.int64)

    # Create a PyVista PolyData mesh.
    mesh = pv.PolyData(vertices, faces_flat)

    # Compute normals using PyVista.
    mesh.compute_normals(cell_normals=True, point_normals=False, inplace=True)
    pv_normals = mesh.cell_normals  # one normal per face (cell)

    differences = []
    print("Comparing face normals:")
    for i, face in enumerate(faces):
        face_vertices = vertices[face]
        # Compute custom normal (from your simulation method)
        custom_norm = custom_calculate_face_normal(face_vertices)
        # Retrieve the PyVista computed normal for this face.
        pv_norm = pv_normals[i]
        # Compute the angular difference between the normals.
        dot_val = np.dot(custom_norm, pv_norm)
        dot_val = np.clip(dot_val, -1, 1)  # avoid floating-point issues
        angle_diff = np.degrees(np.arccos(dot_val))
        differences.append(angle_diff)
        print(f"Face {i}: custom normal = {custom_norm}, PyVista normal = {pv_norm}, angle diff = {angle_diff:.2f}°")

    avg_diff = np.mean(differences)
    print(f"\nAverage normal difference over all faces: {avg_diff:.2f}°")

    # Visualization:
    # Add the computed differences as a cell array so we can color the faces accordingly.
    mesh.cell_arrays['Normal Difference'] = np.array(differences)
    plotter = pv.Plotter()
    plotter.add_mesh(mesh, scalars='Normal Difference', cmap='jet', show_edges=True)
    plotter.add_scalar_bar(title="Angle Difference (°)")
    plotter.add_text(f"Average Difference: {avg_diff:.2f}°", position='upper_left', font_size=12)
    plotter.show()


if __name__ == "__main__":
    compare_normals()
