import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class SensorPhaseViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Sensor Icosahedron Phase Viewer")
        self.setGeometry(100, 100, 900, 700)

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
        sensor_positions = self.get_sensor_positions()
        fov = 60

        self.ax.view_init(elev=30, azim=45)

        vertices, faces = self.get_icosahedron()

        for sensor_position in sensor_positions:
            for face in faces:
                face_vertices = vertices[face]
                face_center = np.mean(face_vertices, axis=0)
                face_normal = self.calculate_face_normal(face_vertices)

                view_vector = sensor_position - face_center
                view_vector /= np.linalg.norm(view_vector)

                dot_product = np.dot(face_normal, view_vector)
                if dot_product > 0:
                    poly = Poly3DCollection([face_vertices], alpha=0.6, edgecolor="black")
                    self.ax.add_collection3d(poly)
                    self.draw_view_frustum(sensor_position, face_center, fov)
                    self.draw_angle_indicators(sensor_position)  # Add the angle indicators

                    distance = np.linalg.norm(sensor_position - face_center)
                    angle = np.degrees(np.arccos(dot_product))
                    offset = face_normal * 1.5
                    annotation_position = face_center + offset
                    self.ax.text(*annotation_position, f"D:{distance:.1f}\nA:{angle:.1f}°",
                                 color='black', fontsize=8, weight='bold',
                                 bbox=dict(facecolor='white', edgecolor='black', alpha=0.7))

            self.ax.scatter(*sensor_position, color='black', label="Sensor", s=80)

        self.ax.set_xlabel("X-axis", fontsize=12)
        self.ax.set_ylabel("Y-axis", fontsize=12)
        self.ax.set_zlabel("Z-axis", fontsize=12)
        self.ax.legend(fontsize=10)
        self.draw()

    def get_sensor_positions(self):
        return np.array([
            [8, 0, 0], [-8, 0, 0],
            [0, 8, 0], [0, -8, 0],
            [0, 0, 8], [0, 0, -8]
        ], dtype=np.float64)

    def calculate_face_normal(self, face_vertices):
        v1, v2, v3 = face_vertices
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)
        return normal / np.linalg.norm(normal)

    def get_icosahedron(self):
        phi = (1 + np.sqrt(5)) / 2
        a, b = 1, phi

        vertices = np.array([[-a, b, 0], [a, b, 0], [-a, -b, 0], [a, -b, 0],
                             [0, -a, b], [0, a, b], [0, -a, -b], [0, a, -b],
                             [b, 0, -a], [b, 0, a], [-b, 0, -a], [-b, 0, a]])
        vertices *= 5 / np.linalg.norm(vertices[0])

        faces = np.array([
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
        ])
        return vertices, faces

    def draw_view_frustum(self, sensor_position, face_center, fov):
        # Calculate the direction from the sensor to the center of the face
        direction = face_center - sensor_position
        direction = direction / np.linalg.norm(direction)

        # Create an arrow pointing from the sensor to the face center
        arrow_length = np.linalg.norm(face_center - sensor_position)
        self.ax.quiver(sensor_position[0], sensor_position[1], sensor_position[2],
                       direction[0], direction[1], direction[2],
                       length=arrow_length, normalize=True, color="black", arrow_length_ratio=0.1)

    def draw_angle_indicators(self, sensor_position, fov_min=30, fov_max=60):
        # Direction of the sensor's optical axis
        direction = np.array([1, 0, 0])  # Assuming camera is oriented along x-axis

        # Compute the transformation for the 30° and 60° angles
        angle_30 = np.deg2rad(fov_min)
        angle_60 = np.deg2rad(fov_max)

        # Create vectors for 30° and 60° directions relative to the camera's optical axis
        vector_30 = self.rotate_vector(direction, angle_30)
        vector_60 = self.rotate_vector(direction, angle_60)

        # Calculate positions for the 30° and 60° angles in space (extend the vectors)
        arrow_length = 10  # Define a suitable length for visualization
        end_position_30 = sensor_position + vector_30 * arrow_length
        end_position_60 = sensor_position + vector_60 * arrow_length

        # Draw lines representing the angles
        self.ax.plot([sensor_position[0], end_position_30[0]],
                     [sensor_position[1], end_position_30[1]],
                     [sensor_position[2], end_position_30[2]], color="blue", linestyle="--")
        self.ax.plot([sensor_position[0], end_position_60[0]],
                     [sensor_position[1], end_position_60[1]],
                     [sensor_position[2], end_position_60[2]], color="red", linestyle="--")

        # Annotate the angles
        self.ax.text(end_position_30[0], end_position_30[1], end_position_30[2],
                     f"30°", color="blue", fontsize=10)
        self.ax.text(end_position_60[0], end_position_60[1], end_position_60[2],
                     f"60°", color="red", fontsize=10)

    def rotate_vector(self, vector, angle):
        """Rotates a vector around the y-axis by a given angle."""
        rotation_matrix = np.array([
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)]
        ])
        return np.dot(rotation_matrix, vector)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())
