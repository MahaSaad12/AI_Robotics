import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection


class SensorPhaseViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Sensor Icosahedron Phase Viewer")
        self.setGeometry(100, 100, 900, 700)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        layout = QVBoxLayout(self.main_widget)

        # Create the table to display distances, angles, and visible faces
        self.table = QTableWidget(self)
        layout.addWidget(self.table)

        self.canvas = PhaseCanvas(self, self.table)  # Pass table reference to PhaseCanvas
        layout.addWidget(NavigationToolbar(self.canvas, self))
        layout.addWidget(self.canvas)

        self.show()


class PhaseCanvas(FigureCanvas):
    def __init__(self, parent=None, table=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        super().__init__(self.fig)
        self.setParent(parent)

        self.table = table  # Store the passed table reference
        self.plot_sensor_and_phases()

    def plot_sensor_and_phases(self):
        sensor_positions = self.get_sensor_positions()
        fov = 60
        self.ax.view_init(elev=30, azim=45)

        vertices, faces = self.get_icosahedron()
        connection_lines = []  # Store sensor-to-face lines

        # Define custom colors for each sensor (red, green, blue, orange, purple, black)
        sensor_colors = ['red', 'green', 'blue', 'orange', 'purple', 'black']

        distances = []  # Store distances
        angles = []  # Store angles
        visible_faces = []  # Store visible face indices
        orientations = []  # Store orientations (alpha, beta, theta)

        for sensor_idx, sensor_position in enumerate(sensor_positions):
            frustum_color = sensor_colors[sensor_idx]  # Assign a color from the list

            for face_idx, face in enumerate(faces):  # Iterate through faces with index
                face_vertices = vertices[face]
                face_center = np.mean(face_vertices, axis=0)
                face_normal = self.calculate_face_normal(face_vertices)

                view_vector = sensor_position - face_center
                view_vector /= np.linalg.norm(view_vector)

                dot_product = np.dot(face_normal, view_vector)
                if dot_product > 0:  # Face is visible to the sensor
                    poly = Poly3DCollection([face_vertices], alpha=0.4, edgecolor="black")
                    self.ax.add_collection3d(poly)

                    # Draw the frustum with the assigned color
                    self.draw_view_frustum(sensor_position, face_center, fov, frustum_color)

                    # Store sensor-to-face connection line
                    connection_lines.append([sensor_position, face_center])

                    # Store visible face index
                    visible_faces.append(face_idx)

                    # Calculate distance and angle
                    distance = np.linalg.norm(sensor_position - face_center)
                    angle = self.calculate_angle(view_vector, face_normal)

                    # Append the distance and angle for the table
                    distances.append(distance)
                    angles.append(angle)

            # Plot the sensor with its assigned color
            self.ax.scatter(*sensor_position, color=frustum_color, label=f"Sensor {sensor_idx + 1}", s=80)

            # Calculate the sensor's orientation after applying rotations
            rotation_matrix = self.get_sensor_rotation(sensor_idx)
            euler_angles = self.rotation_matrix_to_euler_angles(rotation_matrix)
            orientations.append(euler_angles)

        # Draw all sensor-to-face lines with a colormap
        connection_colors = plt.cm.viridis(np.linspace(0, 1, len(connection_lines)))
        line_collection = Line3DCollection(connection_lines, colors=connection_colors, linewidths=1.5, alpha=0.8)
        self.ax.add_collection3d(line_collection)

        # Update the table with the calculated distances, angles, visible faces, and orientations
        self.update_table(distances, angles, visible_faces, orientations)

        # Labels and legend
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

    def calculate_angle(self, view_vector, face_normal):
        cos_angle = np.dot(view_vector, face_normal)
        return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))  # Convert to degrees

    def draw_view_frustum(self, sensor_position, face_center, fov, frustum_color):
        direction = face_center - sensor_position
        direction /= np.linalg.norm(direction)

        # Define frustum end points
        frustum_length = 10
        frustum_end = sensor_position + direction * frustum_length

        # Create frustum lines with thinner width
        frustum_lines = [[sensor_position, frustum_end]]
        line_collection = Line3DCollection(frustum_lines, colors=[frustum_color], linewidths=0.1, alpha=0.8)
        self.ax.add_collection3d(line_collection)

    def update_table(self, distances, angles, visible_faces, orientations):
        if self.table is None:
            print("Error: Table reference is missing!")
            return

        rows = len(distances)
        self.table.setRowCount(rows)
        self.table.setColumnCount(8)  # Add 3 more columns for alpha, beta, theta

        self.table.setHorizontalHeaderLabels(
            ["Sensor", "Pose", "Face", "Distance", "Angle", "Alpha", "Beta", "Theta"]
        )

        sensor_positions = self.get_sensor_positions()

        for i in range(rows):
            # Determine the sensor index and its position
            sensor_idx = i // 10  # Assuming there are 10 visible faces per sensor for simplicity
            sensor_position = sensor_positions[sensor_idx]
            sensor_pose = f"({sensor_position[0]:.2f}, {sensor_position[1]:.2f}, {sensor_position[2]:.2f})"

            # Get the Euler angles (alpha, beta, theta) for the current sensor
            alpha, beta, theta = orientations[sensor_idx]

            # Set the data in the table
            self.table.setItem(i, 0, QTableWidgetItem(f"Sensor {(i // 10) + 1}"))
            self.table.setItem(i, 1, QTableWidgetItem(sensor_pose))
            self.table.setItem(i, 2, QTableWidgetItem(f"Face {visible_faces[i]}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{distances[i]:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{angles[i]:.2f}°"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{alpha:.2f}°"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{beta:.2f}°"))
            self.table.setItem(i, 7, QTableWidgetItem(f"{theta:.2f}°"))

    def get_sensor_rotation(self, sensor_idx):
        # Assign different rotations to each sensor
        if sensor_idx == 0:
            rotation_x = self.rotation_matrix_x(42)
            rotation_z = self.rotation_matrix_z(30)
        elif sensor_idx == 1:
            rotation_x = self.rotation_matrix_x(42)
            rotation_z = self.rotation_matrix_z(60)
        elif sensor_idx == 2:
            rotation_x = self.rotation_matrix_x(42)
            rotation_z = self.rotation_matrix_z(90)
        elif sensor_idx == 3:
            rotation_x = self.rotation_matrix_x(60)
            rotation_z = self.rotation_matrix_z(30)
        elif sensor_idx == 4:
            rotation_x = self.rotation_matrix_x(60)
            rotation_z = self.rotation_matrix_z(60)
        else:
            rotation_x = self.rotation_matrix_x(60)
            rotation_z = self.rotation_matrix_z(90)

        return np.dot(rotation_z, rotation_x)

    def rotation_matrix_x(self, theta):
        """Rotation matrix for rotation around the X-axis."""
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

    def rotation_matrix_z(self, theta):
        """Rotation matrix for rotation around the Z-axis."""
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    def rotation_matrix_to_euler_angles(self, R):
        """Convert rotation matrix to Euler angles (alpha, beta, theta)."""
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)

        singular = sy < 1e-6
        if not singular:
            alpha = np.arctan2(R[2, 1], R[2, 2])
            beta = np.arctan2(-R[2, 0], sy)
            theta = np.arctan2(R[1, 0], R[0, 0])
        else:
            alpha = np.arctan2(-R[1, 2], R[1, 1])
            beta = np.arctan2(-R[2, 0], sy)
            theta = 0
        return np.degrees(np.array([alpha, beta, theta]))


def cross_validate_orientation(sensor_positions, orientations, k=5):
    fold_size = len(sensor_positions) // k
    errors = []

    for i in range(k):
        test_idx = slice(i * fold_size, (i + 1) * fold_size)
        train_idx = np.concatenate([np.arange(0, i * fold_size), np.arange((i + 1) * fold_size, len(sensor_positions))])

        train_orientations = [orientations[idx] for idx in train_idx]
        test_orientations = [orientations[idx] for idx in test_idx]
        test_positions = [sensor_positions[idx] for idx in test_idx]

        # Train the model (in this case, it's just applying rotations)
        predicted_orientations = []
        for position in test_positions:
            # Here, use the `get_sensor_rotation` method (or some model) to predict the orientation
            predicted_rotation_matrix = get_sensor_rotation_from_position(position)
            predicted_euler = rotation_matrix_to_euler_angles(predicted_rotation_matrix)
            predicted_orientations.append(predicted_euler)

        # Calculate the error for this fold
        fold_errors = [
            angular_error(true, predicted)
            for true, predicted in zip(test_orientations, predicted_orientations)
        ]
        errors.append(np.mean(fold_errors))  # Average error for this fold

    # Return the average error across all folds
    return np.mean(errors)
