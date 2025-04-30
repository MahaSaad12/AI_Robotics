import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SensorPhaseViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sensor Phase Viewer")
        self.setGeometry(100, 100, 800, 600)

        # Initialize the main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Create the canvas for the plot
        self.canvas = PhaseCanvas(self, self)

        # Create the table widget to display sensor data
        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(3)  # Columns for sensor label, distance, and angle
        self.table_widget.setHorizontalHeaderLabels(["Sensor-Face", "Distance", "Angle"])

        # Layout setup
        layout = QVBoxLayout(self.main_widget)
        layout.addWidget(self.canvas)
        layout.addWidget(self.table_widget)

        self.show()


class PhaseCanvas(FigureCanvas):
    def __init__(self, parent=None, table_widget=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        super().__init__(self.fig)
        self.setParent(parent)

        self.table_widget = table_widget  # Now table_widget is passed directly here

        self.distances = []  # List to store all distances
        self.angles = []     # List to store all angles

        self.plot_sensor_and_phases()

    def plot_sensor_and_phases(self):
        """This method plots the sensors and the icosahedron faces in the X-Y plane."""
        sensor_positions = self.get_sensor_positions()
        fov = 60  # Field of View

        self.ax.view_init(elev=30, azim=45)  # Set the view angle

        vertices, faces = self.get_icosahedron()

        colors = ['red', 'blue', 'green', 'purple', 'orange', 'cyan']  # Colors for sensors

        # Reset the distances and angles for each new plot
        self.distances.clear()
        self.angles.clear()

        for i, sensor_position in enumerate(sensor_positions):
            # Only consider the X-Y plane for visualization
            sensor_position_2d = sensor_position[:2]  # Only use X and Y for 2D plot

            for j, face in enumerate(faces):
                face_vertices = vertices[face]
                face_center = np.mean(face_vertices, axis=0)
                face_normal = self.calculate_face_normal(face_vertices)

                # Only consider the X-Y plane for visualization of face
                face_center_2d = face_center[:2]

                # Draw the sensor and the face in the X-Y plane (no Z-axis consideration)
                self.ax.scatter(sensor_position_2d[0], sensor_position_2d[1], color=colors[i], label=f"Sensor {i+1}", s=80)

                # Calculate distance and angle to the face center (ignoring Z-axis)
                distance = np.linalg.norm(sensor_position_2d - face_center_2d)
                angle = np.degrees(np.arccos(np.dot(face_normal[:2], (sensor_position_2d - face_center_2d) / distance)))

                # Store the distance and angle for plotting
                sensor_face_label = f"Sensor {i+1} - Face {j+1}"
                self.distances.append((sensor_face_label, distance))
                self.angles.append((sensor_face_label, angle))

            # Plot the line chart of sensor distances based on X-Y plane data
            self.ax.plot([sensor_position_2d[0], face_center_2d[0]],
                         [sensor_position_2d[1], face_center_2d[1]], color=colors[i], linestyle="--")

        # Update the table with all distance and angle data
        self.update_table()

    def update_table(self):
        """Update the table with unique distance and angle data."""
        # Remove duplicates
        unique_distances = []
        seen = set()
        for sensor_face_label, distance in self.distances:
            if (sensor_face_label, distance) not in seen:
                unique_distances.append((sensor_face_label, distance))
                seen.add((sensor_face_label, distance))

        # First, clear any existing data from the table
        self.table_widget.setRowCount(len(unique_distances))  # Resize table to match the data

        # Populate the table with non-repeating data
        for i, (sensor_face_label, distance) in enumerate(unique_distances):
            self.table_widget.setItem(i, 0, QTableWidgetItem(sensor_face_label))
            self.table_widget.setItem(i, 1, QTableWidgetItem(f"{distance:.2f}"))
            self.table_widget.setItem(i, 2, QTableWidgetItem(f"{self.angles[i][1]:.2f}"))

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


if __name__ == "__main__":
    app = QApplication([])
    viewer = SensorPhaseViewerApp()
    app.exec_()
