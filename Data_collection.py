import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class SensorPhaseViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Sensor Icosahedron Phase Viewer with Rotation and Line Chart")
        self.setGeometry(100, 100, 1200, 800)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        layout = QVBoxLayout(self.main_widget)

        # Create a horizontal layout for 3D plot and line chart
        control_layout = QHBoxLayout()

        # Add line chart canvas first
        self.line_chart_canvas = LineChartCanvas(self)  # Create the line chart canvas first
        layout.addWidget(self.line_chart_canvas)

        # Add canvas for 3D plot
        self.canvas = PhaseCanvas(self)
        control_layout.addWidget(self.canvas)

        layout.addLayout(control_layout)

        self.show()


class PhaseCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        super().__init__(self.fig)
        self.setParent(parent)

        self.distances = [[] for _ in range(6)]  # List to store distances for each sensor
        self.angles = [[] for _ in range(6)]  # List to store angles for each sensor

        self.plot_sensor_and_phases()

    def plot_sensor_and_phases(self):
        """This method plots the sensors and the icosahedron faces with annotations for distance and angle."""
        sensor_positions = self.get_sensor_positions()
        fov = 60  # Field of View

        self.ax.view_init(elev=30, azim=45)  # Set the view angle

        vertices, faces = self.get_icosahedron()

        colors = ['red', 'blue', 'green', 'purple', 'orange', 'cyan']  # Colors for sensors

        for i, sensor_position in enumerate(sensor_positions):
            for face in faces:
                face_vertices = vertices[face]
                face_center = np.mean(face_vertices, axis=0)
                face_normal = self.calculate_face_normal(face_vertices)

                # Calculate the vector from the sensor to the face center
                view_vector = sensor_position - face_center
                view_vector /= np.linalg.norm(view_vector)

                # Check visibility
                dot_product = np.dot(face_normal, view_vector)
                if dot_product > 0:
                    # Draw the face if visible
                    poly = Poly3DCollection([face_vertices], alpha=0.6, edgecolor="black")
                    self.ax.add_collection3d(poly)

                    # Draw the frustum (view cone from the sensor)
                    self.draw_view_frustum(sensor_position, face_center, fov)

                    # Calculate distance and angle to the face center
                    distance = np.linalg.norm(sensor_position - face_center)
                    angle = np.degrees(np.arccos(dot_product))

                    # Annotate the distance and angle at the face center
                    offset = face_normal * 1.5  # Position the annotation offset from the face center
                    annotation_position = face_center + offset
                    self.ax.text(*annotation_position, f"D:{distance:.1f}\nA:{angle:.1f}°",
                                 color='black', fontsize=8, weight='bold',
                                 bbox=dict(facecolor='white', edgecolor='black', alpha=0.7))

                    # Collect data for the line chart (distances and angles for each sensor)
                    self.distances[i].append(distance)
                    self.angles[i].append(angle)

            # Plot the sensor position with different colors
            self.ax.scatter(*sensor_position, color=colors[i], label=f"Sensor {i+1}", s=80)

        # Set labels and legend
        self.ax.set_xlabel("X-axis", fontsize=12)
        self.ax.set_ylabel("Y-axis", fontsize=12)
        self.ax.set_zlabel("Z-axis", fontsize=12)
        self.ax.legend(fontsize=10)
        self.draw()

        # Update the line chart with the latest data
        self.parent().line_chart_canvas.update_chart(self.distances, self.angles)

    def get_sensor_positions(self):
        """Define six sensor positions strategically around the icosahedron."""
        return np.array([
            [8, 0, 0], [-8, 0, 0],  # +X and -X
            [0, 8, 0], [0, -8, 0],  # +Y and -Y
            [0, 0, 8], [0, 0, -8]  # +Z and -Z
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

    def draw_view_frustum(self, sensor_position, face_center, fov):
        """Draw a simple view frustum (view cone)."""
        direction = face_center - sensor_position
        direction = direction / np.linalg.norm(direction)

        far_plane = 6  # Define the farthest distance of the frustum
        frustum_end = sensor_position + direction * far_plane
        self.ax.plot([sensor_position[0], frustum_end[0]],
                     [sensor_position[1], frustum_end[1]],
                     [sensor_position[2], frustum_end[2]], color="black", linestyle="--")


class LineChartCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self.distances = [[] for _ in range(6)]
        self.angles = [[] for _ in range(6)]

    def update_chart(self, distances, angles):
        """Update the chart with new distance and angle data."""
        self.distances = distances
        self.angles = angles
        self.ax.cla()  # Clear the axes

        # Plot distance and angle data for each sensor
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'cyan']
        for i in range(6):
            # Plot each sensor's distance and angle on the same chart
            self.ax.plot(self.distances[i], label=f'Sensor {i+1} - Distance', color=colors[i], marker='o')
            self.ax.plot(self.angles[i], label=f'Sensor {i+1} - Angle', color=colors[i], marker='x')

        # Set the labels for the axes
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Distance / Angle")
        self.ax.legend()
        self.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())
