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

        for sensor_idx, sensor_position in enumerate(sensor_positions):
            frustum_color = sensor_colors[sensor_idx]  # Assign a color from the list

            sensor_visible_faces = []  # Store faces visible to this sensor

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
                    sensor_visible_faces.append(face_idx)

                    # Calculate distance and angle
                    distance = np.linalg.norm(sensor_position - face_center)
                    angle = self.calculate_angle(view_vector, face_normal)

                    # Append the distance and angle for the table
                    distances.append(distance)
                    angles.append(angle)

            # Plot the sensor with its assigned color
            self.ax.scatter(*sensor_position, color=frustum_color, label=f"Sensor {sensor_idx + 1}", s=80)
            visible_faces.append(sensor_visible_faces)

        # Draw all sensor-to-face lines with a colormap
        connection_colors = plt.cm.viridis(np.linspace(0, 1, len(connection_lines)))
        line_collection = Line3DCollection(connection_lines, colors=connection_colors, linewidths=1.5, alpha=0.8)
        self.ax.add_collection3d(line_collection)

        # Update the table with the calculated distances, angles, and face visibility
        self.update_table(distances, angles, visible_faces)

        # Labels and legend
        self.ax.set_xlabel("X-axis", fontsize=12)
        self.ax.set_ylabel("Y-axis", fontsize=12)
        self.ax.set_zlabel("Z-axis", fontsize=12)
        self.ax.legend(fontsize=10)
        self.draw()

        # Evaluate the coverage/view plan
        total_faces = len(faces)
        score = evaluate_coverage_view_plan(sensor_positions, visible_faces, distances, angles, total_faces)
        print(f"Coverage/View Plan Score: {score}")

    def get_sensor_positions(self):
        return np.array([  # Define the positions of the 6 sensors
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

        faces = np.array([  # The faces of the icosahedron
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

    def update_table(self, distances, angles, visible_faces):
        if self.table is None:
            print("Error: Table reference is missing!")
            return

        rows = len(distances)
        self.table.setRowCount(rows)
        self.table.setColumnCount(4)  # 4 columns: Sensor, Face Index, Distance, Angle

        self.table.setHorizontalHeaderLabels(["Sensor", "Face", "Distance", "Angle"])

        # Flatten the visible_faces list for use in the table
        flat_visible_faces = [face for sublist in visible_faces for face in sublist]

        for i in range(rows):
            sensor_index = (i // 6) + 1  # Determine the sensor number
            face_index = flat_visible_faces[i] if i < len(
                flat_visible_faces) else "N/A"  # Handle cases with missing data
            self.table.setItem(i, 0, QTableWidgetItem(f"Sensor {sensor_index}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"Face {face_index}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{distances[i]:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{angles[i]:.2f}°"))

def evaluate_coverage_view_plan(sensors_positions, visible_faces, distances, angles, total_faces):

    unique_visible_faces = set()
    for faces in visible_faces:
        unique_visible_faces.update(faces)

    coverage_score = len(unique_visible_faces) / total_faces  # Maximize the fraction of covered faces

    # Minimize the total distance from each sensor to its visible faces
    total_distance = np.sum(distances)  # Lower is better

    # Minimize the sum of angles between sensor views and face normals (penalizing larger angles)
    angle_penalty = np.sum([1 / (1 + np.cos(np.radians(angle))) for angle in angles])  # Penalize larger angles

    # Calculate the overlap penalty: how much overlap there is in visible faces
    overlap_penalty = 0
    for i in range(len(visible_faces)):
        for j in range(i + 1, len(visible_faces)):
            overlap_penalty += len(set(visible_faces[i]) & set(visible_faces[j]))  # Count shared visible faces

    # We want to maximize coverage, minimize distance, minimize angle, and reduce overlap
    objective_value = coverage_score - (total_distance / 100) - angle_penalty - (overlap_penalty / 10)

    return objective_value


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())
