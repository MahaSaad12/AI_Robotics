import sys
import time
import gc
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer
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

        self.table = QTableWidget(self)
        layout.addWidget(self.table)

        self.canvas = PhaseCanvas(self, self.table)
        layout.addWidget(NavigationToolbar(self.canvas, self))
        layout.addWidget(self.canvas)

        self.show()


class PhaseCanvas(FigureCanvas):
    def __init__(self, parent=None, table=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        super().__init__(self.fig)
        self.setParent(parent)
        self.table = table

        self._updating = False  # reentrancy flag

        # Use a QTimer to update the scene every 3000 ms.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(3000)

        # Define a list of unique sensor colors (for 6 sensors in this example)
        self.unique_sensor_colors = ['red', 'green', 'blue', 'orange', 'purple', 'magenta']

    def update_scene(self):
        if self._updating:
            return
        self._updating = True
        try:
            # Clear the figure and collect garbage to reduce resource buildup.
            self.fig.clf()
            gc.collect()
            self.ax = self.fig.add_subplot(111, projection="3d")
            self.ax.view_init(elev=30, azim=45)

            sensor_positions = self.get_sensor_positions()
            fov = 60
            vertices, faces = self.get_icosahedron()
            connection_lines = []

            # Lists for table update
            distances = []
            angles = []
            visible_faces = []
            orientations = []  # (alpha, beta, theta) per sensor
            sensor_status = []
            sensor_indices = []

            # Loop through each sensor
            for sensor_idx, sensor_position in enumerate(sensor_positions):
                rotation_matrix, visible_count, face_data = self.get_sensor_rotation(sensor_idx)
                if rotation_matrix is None:
                    rotation_matrix = np.eye(3)

                # Get unique sensor color from the predefined list:
                sensor_color = self.unique_sensor_colors[sensor_idx % len(self.unique_sensor_colors)]

                alpha, beta, theta = self.rotation_matrix_to_euler_angles(rotation_matrix)
                orientations.append((alpha, beta, theta))
                status = "GOOD" if visible_count >= 5 else "BAD"
                sensor_status.append(status)

                # Use the unique sensor_color for all drawing instead of color based on status.
                for face_idx, distance, angle, face_center in face_data:
                    face_vertices = vertices[faces[face_idx]]
                    poly = Poly3DCollection([face_vertices], alpha=0.4, edgecolor="black")
                    self.ax.add_collection3d(poly)

                    self.draw_view_frustum(sensor_position, face_center, fov, sensor_color)
                    connection_lines.append([sensor_position, face_center])

                    visible_faces.append(face_idx)
                    distances.append(distance)
                    angles.append(angle)
                    sensor_indices.append(sensor_idx)

                self.ax.scatter(*sensor_position, color=sensor_color, label=f"Sensor {sensor_idx + 1}", s=80)

            connection_colors = plt.cm.viridis(np.linspace(0, 1, len(connection_lines)))
            line_collection = Line3DCollection(connection_lines, colors=connection_colors,
                                               linewidths=1.5, alpha=0.8)
            self.ax.add_collection3d(line_collection)
            self.ax.set_xlabel("X-axis", fontsize=12)
            self.ax.set_ylabel("Y-axis", fontsize=12)
            self.ax.set_zlabel("Z-axis", fontsize=12)
            self.ax.legend(fontsize=10)

            self.update_table(distances, angles, visible_faces, orientations, sensor_status, sensor_indices)
            self.draw_idle()  # Schedule a redraw
        except Exception as e:
            print("Error during update_scene:", e)
        finally:
            self._updating = False

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

    def calculate_angle(self, vec1, vec2):
        cos_angle = np.dot(vec1, vec2)
        return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    def draw_view_frustum(self, sensor_position, face_center, fov, frustum_color):
        direction = face_center - sensor_position
        direction /= np.linalg.norm(direction)
        frustum_length = 10
        frustum_end = sensor_position + direction * frustum_length
        frustum_lines = [[sensor_position, frustum_end]]
        line_collection = Line3DCollection(frustum_lines, colors=[frustum_color],
                                           linewidths=0.5, alpha=0.8)
        self.ax.add_collection3d(line_collection)

    def update_table(self, distances, angles, visible_faces, orientations, status_list, sensor_indices):
        if self.table is None:
            print("Error: Table reference is missing!")
            return
        rows = len(distances)
        self.table.setRowCount(rows)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["Sensor", "Pose", "Face", "Distance", "Angle", "Alpha", "Beta", "Theta", "Status"]
        )
        sensor_positions = self.get_sensor_positions()
        for i in range(rows):
            sensor_idx = sensor_indices[i]
            sensor_position = sensor_positions[sensor_idx]
            pose = f"({sensor_position[0]:.2f}, {sensor_position[1]:.2f}, {sensor_position[2]:.2f})"
            alpha, beta, theta = orientations[sensor_idx]
            status = status_list[sensor_idx]
            self.table.setItem(i, 0, QTableWidgetItem(f"Sensor {sensor_idx + 1}"))
            self.table.setItem(i, 1, QTableWidgetItem(pose))
            self.table.setItem(i, 2, QTableWidgetItem(f"Face {visible_faces[i]}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{distances[i]:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{angles[i]:.2f}°"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{alpha:.2f}°"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{beta:.2f}°"))
            self.table.setItem(i, 7, QTableWidgetItem(f"{theta:.2f}°"))
            self.table.setItem(i, 8, QTableWidgetItem(status))

    def get_sensor_rotation(self, sensor_idx):
        fov = 60
        max_visible = 0
        best_data = []
        sensor_position = self.get_sensor_positions()[sensor_idx]
        base_view = -sensor_position / np.linalg.norm(sensor_position)
        # Get dynamic calibration object rotation (using system time)
        object_rot = self.get_calibration_object_rotation()
        rotated_view = object_rot @ base_view
        vertices, faces = self.get_icosahedron()
        for idx, face in enumerate(faces):
            face_vertices = vertices[face]
            face_center = np.mean(face_vertices, axis=0)
            view_vector = face_center - sensor_position
            view_vector /= np.linalg.norm(view_vector)
            angle = self.calculate_angle(view_vector, rotated_view)
            if angle < fov / 2:
                distance = np.linalg.norm(face_center - sensor_position)
                best_data.append((idx, distance, angle, face_center))
                max_visible += 1
        return object_rot, max_visible, best_data

    def get_calibration_object_rotation(self):
        # Simulate live rotation of the calibration object:
        # Rotating around Y at 30°/sec and around X at 20°/sec.
        angle_y = (time.time() * 30) % 360
        angle_x = (time.time() * 20) % 360
        Ry = self.rotation_matrix_y(angle_y)
        Rx = self.rotation_matrix_x(angle_x)
        return Rx @ Ry

    def rotation_matrix_x(self, theta):
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[1, 0, 0],
                         [0, c, -s],
                         [0, s, c]])

    def rotation_matrix_y(self, theta):
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[c, 0, s],
                         [0, 1, 0],
                         [-s, 0, c]])

    def rotation_matrix_z(self, theta):
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[c, -s, 0],
                         [s, c, 0],
                         [0, 0, 1]])

    def rotation_matrix_to_euler_angles(self, R):
        alpha = np.arctan2(R[2, 1], R[2, 2])
        beta = np.arctan2(-R[2, 0], np.sqrt(R[2, 1] ** 2 + R[2, 2] ** 2))
        theta = np.arctan2(R[1, 0], R[0, 0])
        return np.degrees(alpha), np.degrees(beta), np.degrees(theta)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())
