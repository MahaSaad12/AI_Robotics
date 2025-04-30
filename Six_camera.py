import sys
import numpy as np
import itertools
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
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
        # Define sensor positions around the icosahedron
        sensor_positions = self.get_sensor_positions()
        look_at = np.array([0, 0, 0])  # Sensors are looking at the icosahedron center
        fov = 60  # Field of view (degrees)

        # Adjust the view angle
        self.ax.view_init(elev=30, azim=45)

        # Draw the icosahedron
        vertices, faces = self.get_icosahedron()

        # Define unique colors for different sensors
        colors = itertools.cycle(["red", "blue", "green", "purple", "brown", "magenta"])

        for sensor_position, color in zip(sensor_positions, colors):
            self.draw_view_frustum(sensor_position, look_at, fov, color)

            # Check and plot visible faces
            for face in faces:
                face_vertices = vertices[face]
                face_center = np.mean(face_vertices, axis=0)
                face_normal = self.calculate_face_normal(face_vertices)

                # Calculate view vector from the sensor to the face center
                view_vector = sensor_position - face_center
                view_vector /= np.linalg.norm(view_vector)  # Normalize

                # Check visibility using the dot product
                dot_product = np.dot(face_normal, view_vector)
                if dot_product > 0:  # Face is visible
                    poly = Poly3DCollection([face_vertices], alpha=0.6, color=color, edgecolor="black")
                    self.ax.add_collection3d(poly)

                    # Annotate distance and angle
                    distance = np.linalg.norm(sensor_position - face_center)
                    angle = np.degrees(np.arccos(dot_product))
                    offset = face_normal * 1.5
                    annotation_position = face_center + offset
                    self.ax.text(*annotation_position, f"D:{distance:.1f}\nA:{angle:.1f}°",
                                 color=color, fontsize=8, weight='bold',
                                 bbox=dict(facecolor='white', edgecolor=color, alpha=0.7))

            # Plot the sensor position
            self.ax.scatter(*sensor_position, color=color, label=f"Sensor {color}", s=80)

        # Set labels and legend
        self.ax.set_xlabel("X-axis", fontsize=12)
        self.ax.set_ylabel("Y-axis", fontsize=12)
        self.ax.set_zlabel("Z-axis", fontsize=12)
        self.ax.legend(fontsize=10)

        # Render plot
        self.draw()

    def get_sensor_positions(self):
        """Define six sensor positions strategically around the icosahedron."""
        return np.array([
            [8, 0, 0], [-8, 0, 0],  # +X and -X
            [0, 8, 0], [0, -8, 0],  # +Y and -Y
            [0, 0, 8], [0, 0, -8]   # +Z and -Z
        ], dtype=np.float64)

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

        faces = np.array([
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
        ])
        return vertices, faces

    def draw_view_frustum(self, sensor_position, look_at, fov, color):
        """Draw a simple view frustum."""
        direction = look_at - sensor_position
        direction = direction / np.linalg.norm(direction)

        far_plane = 6  # Define the farthest distance of the frustum
        frustum_end = sensor_position + direction * far_plane
        self.ax.plot([sensor_position[0], frustum_end[0]],
                     [sensor_position[1], frustum_end[1]],
                     [sensor_position[2], frustum_end[2]], color=color, linestyle="--")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())
