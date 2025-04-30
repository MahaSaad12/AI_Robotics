import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SensorPhaseViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Sensor Distance & Angle Histograms")
        self.setGeometry(100, 100, 1200, 800)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        layout = QVBoxLayout(self.main_widget)

        # Create a horizontal layout for histograms
        chart_layout = QHBoxLayout()

        # Add distance histogram
        self.distance_chart_canvas = DistanceHistogramCanvas(self)
        chart_layout.addWidget(self.distance_chart_canvas)

        # Add angle histogram
        self.angle_chart_canvas = AngleHistogramCanvas(self)
        chart_layout.addWidget(self.angle_chart_canvas)

        layout.addLayout(chart_layout)

        # Generate and update sensor data
        self.generate_sensor_data()

        self.show()

    def generate_sensor_data(self):
        """Generates distance and angle data for sensors and updates the histograms."""
        num_sensors = 6
        num_points = 20  # Number of data points per sensor

        distances = [np.random.uniform(2, 10, num_points).tolist() for _ in range(num_sensors)]
        angles = [np.random.uniform(0, 90, num_points).tolist() for _ in range(num_sensors)]

        # Save data to CSV files
        self.save_data_to_csv("../Testing/sensor_distances.csv", distances, "Distance")
        self.save_data_to_csv("sensor_angles.csv", angles, "Angle")

        # Update histograms
        self.distance_chart_canvas.update_chart(distances)
        self.angle_chart_canvas.update_chart(angles)

    def save_data_to_csv(self, filename, data, label):
        """Saves sensor data to a CSV file."""
        num_sensors = len(data)
        num_points = len(data[0])

        data_dict = {"Index": list(range(1, num_points + 1))}
        for i in range(num_sensors):
            data_dict[f"Sensor {i+1}"] = data[i]

        df = pd.DataFrame(data_dict)
        df.to_csv(filename, index=False)
        print(f"{label} data saved to {filename}")

class DistanceHistogramCanvas(FigureCanvas):
    """Histogram for sensor distances."""
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

    def update_chart(self, distances):
        """Updates the histogram with new distance data (in meters)."""
        self.ax.cla()
        all_distances = [val for sublist in distances for val in sublist]
        self.ax.hist(all_distances, bins=10, color='blue', edgecolor='black', alpha=0.7)
        self.ax.set_title("Sensor Distance Histogram")
        self.ax.set_xlabel("Distance (meters)")  # Explicitly mention meters
        self.ax.set_ylabel("Frequency")
        self.draw()

class AngleHistogramCanvas(FigureCanvas):
    """Histogram for sensor angles."""
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

    def update_chart(self, angles):
        """Updates the histogram with new angle data."""
        self.ax.cla()
        all_angles = [val for sublist in angles for val in sublist]
        self.ax.hist(all_angles, bins=10, color='red', edgecolor='black', alpha=0.7)
        self.ax.set_title("Sensor Angle Histogram")
        self.ax.set_xlabel("Angle (°)")
        self.ax.set_ylabel("Frequency")
        self.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SensorPhaseViewerApp()
    sys.exit(app.exec_())
