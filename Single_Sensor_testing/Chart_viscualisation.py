import sys
import numpy as np
import itertools
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar
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

        # Create a horizontal layout for sliders and the 3D plot
        control_layout = QHBoxLayout()

        # Add sliders for controlling the position of the sensor
        self.x_slider = self.create_slider("X Position", control_layout)
        self.y_slider = self.create_slider("Y Position", control_layout)
        self.z_slider = self.create_slider("Z Position", control_layout)

        # Add sliders for rotating the icosahedron
        self.rotation_x_slider = self.create_slider("Rotation X", control_layout, min_val=-180, max_val=180)
        self.rotation_y_slider = self.create_slider("Rotation Y", control_layout, min_val=-180, max_val=180)
        self.rotation_z_slider = self.create_slider("Rotation Z", control_layout, min_val=-180, max_val=180)

        # Add canvas for 3D plot
        self.canvas = PhaseCanvas(self)
        control_layout.addWidget(self.canvas)

        # Add line chart for distance and angle
        self.line_chart_canvas = LineChartCanvas(self)
        layout.addLayout(control_layout)
        layout.addWidget(self.line_chart_canvas)

        self.show()

    def create_slider(self, label_text, layout, min_val=-10, max_val=10):
        slider_layout = QVBoxLayout()
        label = QLabel(label_text)
        slider_layout.addWidget(label)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(0)
        slider.valueChanged.connect(self.update_sensor_position)
        slider_layout.addWidget(slider)

        layout.addLayout(slider_layout)
        return slider

    def update_sensor_position(self):
        # Get new sensor position from the sliders
        x = self.x_slider.value()
        y = self.y_slider.value()
        z = self.z_slider.value()

        # Get new rotation angles from the rotation sliders
        rotation_x = np.radians(self.rotation_x_slider.value())
        rotation_y = np.radians(self.rotation_y_slider.value())
        rotation_z = np.radians(self.rotation_z_slider.value())

        self.canvas.update_sensor_position(np.array([x, y, z]), rotation_x, rotation_y, rotation_z)
        self.line_chart_canvas.update_chart(self.canvas.distances, self.canvas.angles)


class PhaseCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        super().__init__(self.fig)
        self.setParent(parent)

        self.sensor_position = np.array([8, 0, 0])  # Initial sensor position
        self.distances = []  # To store distance data
        self.angles = []  # To store angle data
        self.rotation_matrix = np.eye(3)  # Initial rotation matrix (identity)

        self.plot_sensor_and_phases()

    def update_sensor_position(self, new_position, rotation_x, rotation_y, rotation_z):
        """Update the sensor position, rotation, and redraw the plot."""
        self.sensor_position = new_position
        self.rotation_matrix = self.get_rotation_matrix(rotation_x, rotation_y, rotation_z)
        self.ax.cla()  # Clear the axes
        self.plot_sensor_and_phases()  # Redraw the plot with updated sensor position and rotation

    def plot_sensor_and_phases(self):
        # Define sensor positions around the icosahedron
        sensor_position = self.sensor_position
        look_at = np.array([0, 0, 0])  # Sensors are looking at the icosahedron center
        fov = 60  # Field of view (degrees)

        # Adjust the view angle
        self.ax.view_init(elev=30, azim=45)

        # Draw the icosahedron
        vertices, faces = self.get_icosahedron()

        # Apply rotation matrix to vertices
        rotated_vertices = np.dot(vertices, self.rotation_matrix.T)

        # Define unique colors for different sensors
        colors = itertools.cycle(["red", "blue", "green", "purple", "brown", "magenta"])

        for sensor_position, color in zip([sensor_position], colors):
            self.draw_view_frustum(sensor_position, look_at, fov, color)

            # Check and plot visible faces
            for face in faces:
                face_vertices = rotated_vertices[face]
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

                    # Collect data for graphing
                    self.distances.append(distance)
                    self.angles.append(angle)

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

    def get_rotation_matrix(self, rotation_x, rotation_y, rotation_z):
        """Generate the rotation matrix based on Euler angles."""
        # Rotation around X-axis
        Rx = np.array([[1, 0, 0],
                       [0, np.cos(rotation_x), -np.sin(rotation_x)],
                       [0, np.sin(rotation_x), np.cos(rotation_x)]])

        # Rotation around Y-axis
        Ry = np.array([[np.cos(rotation_y), 0, np.sin(rotation_y)],
                       [0, 1, 0],
                       [-np.sin(rotation_y), 0, np.cos(rotation_y)]])

        # Rotation around Z-axis
        Rz = np.array([[np.cos(rotation_z), -np.sin(rotation_z), 0],
                       [np.sin(rotation_z), np.cos(rotation_z), 0],
                       [0, 0, 1]])

        # Combined rotation matrix
        return np.dot(Rz, np.dot(Ry, Rx))

    def draw_view_frustum(self, sensor_position, look_at, fov, color):
        """Draw a simple view frustum."""
        direction = look_at - sensor_position
        direction = direction / np.linalg.norm(direction)

        far_plane = 6  # Define the farthest distance of the frustum
        frustum_end = sensor_position + direction * far_plane
        self.ax.plot([sensor_position[0], frustum_end[0]],
                     [sensor_position[1], frustum_end[1]],
                     [sensor_position[2], frustum_end[2]], color=color, linestyle="--")


class LineChartCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self.distances = []
        self.angles = []

    def update_chart(self, distances, angles):
        """Update the chart with new distance and angle data."""
        self.distances = distances
        self.angles = angles
        self.ax.cla()  # Clear the axes

        # Plot distance and angle data
        self.ax.plot(self.distances, label='Distance', color='blue', marker='o')
        self.ax.plot(self.angles, label='Angle', color='red', marker='x')

        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Distance / Angle")
        self.ax.legend()
        self.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())
