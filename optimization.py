import sys
import time
import gc
import csv
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection


class SensorPhaseViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Sensor Icosahedron Phase Viewer")
        self.setGeometry(100, 100, 1000, 700)

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
        self._updating = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(3000)

        self.unique_sensor_colors = ['red', 'green', 'blue', 'orange', 'purple', 'magenta']
        self.expected_visible_faces = {
            0: [0, 1, 5], 1: [3, 4, 10], 2: [6, 7, 8],
            3: [9, 10, 11], 4: [12, 13, 14], 5: [15, 16, 17]
        }

    def update_scene(self):
        if self._updating:
            return
        self._updating = True
        try:
            self.fig.clf()
            gc.collect()
            self.ax = self.fig.add_subplot(111, projection="3d")
            self.ax.view_init(elev=30, azim=45)

            sensor_positions = self.get_sensor_positions()
            fov = 60
            vertices, faces = self.get_icosahedron()
            connection_lines = []

            distances, angles, visible_faces = [], [], []
            orientations, sensor_status, sensor_indices, scores = [], [], [], []

            # Prepare CSV data
            csv_data = []

            for sensor_idx, sensor_position in enumerate(sensor_positions):
                rot_mat, visible_count, face_data = self.get_sensor_rotation(sensor_idx)
                sensor_color = self.unique_sensor_colors[sensor_idx % len(self.unique_sensor_colors)]

                alpha, beta, theta = self.rotation_matrix_to_euler_angles(rot_mat)
                orientations.append((alpha, beta, theta))
                status = "GOOD" if visible_count >= 5 else "BAD"
                sensor_status.append(status)

                actual_faces = set([f[0] for f in face_data])
                expected_faces = set(self.expected_visible_faces.get(sensor_idx, []))
                score = len(actual_faces & expected_faces) / max(len(expected_faces), 1)
                scores.append(score)

                if actual_faces != expected_faces:
                    print(f"[Sensor {sensor_idx}] MISMATCH: Expected {expected_faces}, Got {actual_faces}")

                for face_idx, distance, angle, face_center in face_data:
                    face_vertices = vertices[faces[face_idx]]
                    poly = Poly3DCollection([face_vertices], alpha=0.4, edgecolor="black")
                    self.ax.add_collection3d(poly)
                    self.draw_view_frustum(sensor_position, face_center, fov, sensor_color)
                    self.draw_face_normal(face_center, self.calculate_face_normal(face_vertices))
                    connection_lines.append([sensor_position, face_center])

                    visible_faces.append(face_idx)
                    distances.append(distance)
                    angles.append(angle)
                    sensor_indices.append(sensor_idx)

                    csv_data.append([
                        f"Sensor {sensor_idx + 1}",
                        f"({sensor_position[0]:.1f}, {sensor_position[1]:.1f}, {sensor_position[2]:.1f})",
                        face_idx,
                        f"{distance:.2f}",
                        f"{angle:.2f}",
                        f"{alpha:.2f}",
                        f"{beta:.2f}",
                        f"{theta:.2f}",
                        status,
                        f"{score:.2f}"
                    ])

                avg_angle = np.mean([a for _, _, a, _ in face_data])
                avg_dist = np.mean([d for _, d, _, _ in face_data])
                print(f"Sensor {sensor_idx + 1}: {visible_count} visible | Avg Angle: {avg_angle:.2f}° | Avg Dist: {avg_dist:.2f}")

                self.ax.scatter(*sensor_position, color=sensor_color, label=f"Sensor {sensor_idx + 1}", s=80)

            self.ax.add_collection3d(Line3DCollection(connection_lines, linewidths=1.5, alpha=0.8))
            self.ax.set_xlabel("X")
            self.ax.set_ylabel("Y")
            self.ax.set_zlabel("Z")
            self.ax.legend(fontsize=10)

            self.update_table(distances, angles, visible_faces, orientations, sensor_status, sensor_indices, scores)
            self.write_to_csv(csv_data)
            self.draw_idle()
        finally:
            self._updating = False

    def write_to_csv(self, data):
        with open("visibility_results.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Sensor", "Pose", "Face", "Distance", "Angle", "Alpha", "Beta", "Theta", "Status", "Score"])
            writer.writerows(data)

    # ... rest of the class remains unchanged (other methods) ...


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())