
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class SensorPhaseViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor and Icosahedron Phase Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        layout = QVBoxLayout(self.main_widget)
        self.canvas = PhaseCanvas(self)
        layout.addWidget(NavigationToolbar(self.canvas, self))
        layout.addWidget(self.canvas)

        self.show()


class PhaseCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        super().__init__(self.fig)
        self.setParent(parent)

        self.plot_sensor_and_phases()

    def plot_sensor_and_phases(self):
        # Find the best sensor position
        sensor_position = self.select_best_viewpoint()
        look_at = np.array([0, 0, 0], dtype=np.float64)  # Sensor is looking at the center of the icosahedron
        fov = 60  # Field of view (degrees)

        # Adjust the view (view angle) to get the best possible view
        self.ax.view_init(elev=30, azim=45)  # Set the viewing angle for optimal view

        # Draw the view frustum
        self.draw_view_frustum(sensor_position, look_at, fov)

        # Icosahedron vertices and faces
        vertices, faces = self.get_icosahedron()

        # Plot the icosahedron and annotate phases (frontal face(s) only)
        for face_idx, face in enumerate(faces):
            face_vertices = vertices[face]
            face_center = np.mean(face_vertices, axis=0)
            face_normal = self.calculate_face_normal(face_vertices)

            # Calculate view vector from the sensor to the face center
            view_vector = sensor_position - face_center
            view_vector /= np.linalg.norm(view_vector)  # Normalize the vector

            # Check if the face is visible (dot product > 0 means facing the sensor)
            dot_product = np.dot(face_normal, view_vector)
            if dot_product > 0:  # Face is visible
                poly = Poly3DCollection([face_vertices], alpha=0.6, color="orange", edgecolor="black")
                self.ax.add_collection3d(poly)

                # Annotate distance and angle
                distance = np.linalg.norm(sensor_position - face_center)
                angle = np.degrees(np.arccos(dot_product))
                offset = face_normal * 1.5
                annotation_position = face_center + offset
                self.ax.text(*annotation_position,
                             f"D:{distance:.1f}\nA:{angle:.1f}°",
                             color="blue", fontsize=10, weight='bold',
                             bbox=dict(facecolor='white', edgecolor='blue', alpha=0.7))

        # Plot the sensor
        self.ax.scatter(*sensor_position, color="green", label="Sensor", s=100)

        # Plot sensor's viewing direction
        self.ax.quiver(*sensor_position, -sensor_position[0], -sensor_position[1], -sensor_position[2],
                       color="red", length=5, arrow_length_ratio=0.2, label="Viewing Direction")

        # Set plot labels and legend
        self.ax.set_xlabel("X-axis", fontsize=12)
        self.ax.set_ylabel("Y-axis", fontsize=12)
        self.ax.set_zlabel("Z-axis", fontsize=12)
        self.ax.legend(fontsize=10)

        # Draw plot
        self.draw()

    def select_best_viewpoint(self):
        """Select the best viewpoint by maximizing the visibility of icosahedron faces."""
        # Icosahedron vertices and faces
        vertices, faces = self.get_icosahedron()

        # Initial sensor position at the origin (center)
        initial_position = np.array([10.0, 0.0, 0.0], dtype=np.float64)  # Starting position on the sphere
        initial_visible_faces = self.evaluate_visible_faces(initial_position, vertices, faces)

        # Start with the initial position
        candidate_positions = [(initial_position, initial_visible_faces)]

        # Define step size and iteration parameters
        step_size = 1.0  # Step size for position adjustment
        max_iterations = 50  # Maximum iterations for the optimization
        num_candidates_to_keep = 10  # Keep only the best 10 candidates

        for iteration in range(max_iterations):
            # Generate new candidate positions by adjusting existing candidates
            new_positions = []
            for position, visible_faces in candidate_positions:
                for _ in range(5):  # Generate 5 random adjustments per candidate
                    random_adjustment = np.random.uniform(-1, 1, 3)
                    new_position = position + random_adjustment * step_size
                    new_position = new_position / np.linalg.norm(new_position) * 10  # Project onto sphere
                    visible_faces = self.evaluate_visible_faces(new_position, vertices, faces)
                    new_positions.append((new_position, visible_faces))

            # Combine old and new positions, and sort by visibility
            candidate_positions += new_positions
            candidate_positions = sorted(candidate_positions, key=lambda x: x[1], reverse=True)  # Sort by visible faces

            # Keep only the top candidates based on visible faces
            candidate_positions = candidate_positions[:num_candidates_to_keep]

        # Return the best position (the one with the most visible faces)
        best_position, _ = candidate_positions[0]
        return best_position

    def evaluate_visible_faces(self, sensor_position, vertices, faces):
        """Evaluate how many faces of the icosahedron are visible from the sensor position."""
        visible_faces = 0
        for face in faces:
            face_vertices = vertices[face]
            face_normal = self.calculate_face_normal(face_vertices)

            # Calculate the vector from the sensor to the face center
            face_center = np.mean(face_vertices, axis=0)
            view_vector = sensor_position - face_center
            view_vector /= np.linalg.norm(view_vector)  # Ensure the view vector is normalized

            # Check if the face is visible (if the angle between the view vector and normal is small)
            dot_product = np.dot(face_normal, view_vector)
            if dot_product > 0:  # Face is visible
                visible_faces += 1

        return visible_faces

    def calculate_face_normal(self, face_vertices):
        """Calculate the normal vector of a triangular face."""
        v1, v2, v3 = face_vertices
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)
        return normal / np.linalg.norm(normal)

    def get_icosahedron(self):
        """Generate icosahedron vertices and faces."""
        phi = (1 + np.sqrt(5)) / 2  # Golden ratio
        a, b = 1, phi

        vertices = np.array([[-a, b, 0], [a, b, 0], [-a, -b, 0], [a, -b, 0],
                             [0, -a, b], [0, a, b], [0, -a, -b], [0, a, -b],
                             [b, 0, -a], [b, 0, a], [-b, 0, -a], [-b, 0, a]])
        vertices *= 5 / np.linalg.norm(vertices[0])  # Scale to size 5

        faces = [
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
        ]
        return np.array(vertices), np.array(faces)

    def draw_view_frustum(self, sensor_position, look_at, fov):
        """Draw a view frustum to represent the camera's field of view."""
        direction = look_at - sensor_position
        direction = direction / np.linalg.norm(direction)  # Normalize direction

        near_plane = 0.25
        far_plane = 3
        aspect_ratio = 1.5

        near_height = 2 * np.tan(np.radians(fov / 2)) * near_plane
        near_width = near_height * aspect_ratio

        far_height = 2 * np.tan(np.radians(fov / 2)) * far_plane
        far_width = far_height * aspect_ratio

        frustum_points = [
            [-near_width / 2, -near_height / 2, near_plane],
            [near_width / 2, -near_height / 2, near_plane],
            [near_width / 2, near_height / 2, near_plane],
            [-near_width / 2, near_height / 2, near_plane],
            [-far_width / 2, -far_height / 2, far_plane],
            [far_width / 2, -far_height / 2, far_plane],
            [far_width / 2, far_height / 2, far_plane],
            [-far_width / 2, far_height / 2, far_plane],
        ]
        frustum_points = np.array(frustum_points)

        R = self.rotation_matrix_from_vectors(np.array([0, 0, 1]), direction)
        frustum_world = (R @ frustum_points.T).T + sensor_position

        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        for edge in edges:
            p1, p2 = frustum_world[edge[0]], frustum_world[edge[1]]
            self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], color="green", alpha=0.6)

    def rotation_matrix_from_vectors(self, vec1, vec2):
        """Compute the rotation matrix to rotate vec1 to vec2."""
        a, b = vec1 / np.linalg.norm(vec1), vec2 / np.linalg.norm(vec2)
        v = np.cross(a, b)
        c = np.dot(a, b)
        if np.allclose(v, 0):  # If vec1 and vec2 are nearly parallel
            return np.eye(3)
        else:
            kmat = np.array([
                [0, -v[2], v[1]],
                [v[2], 0, -v[0]],
                [-v[1], v[0], 0]
            ])
            return np.eye(3) + kmat + np.outer(v, v) * (1 - c) / (np.linalg.norm(v) ** 2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())
