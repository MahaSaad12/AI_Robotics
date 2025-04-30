import numpy as np


class OptimizedSensorRotation:
    def __init__(self):
        self.precision = np.float64  # Use high precision for calculations

        # Precompute the X-axis rotation matrix (fixed 42 degrees)
        self.rotation_x = self.rotation_matrix_x(42).astype(self.precision)

        # Define Z-axis rotation values for each sensor (specific to the sensor)
        self.z_rotations = [30, 60, 90, 120, 150, 180]  # Predefined Z-axis angles

        # Precompute rotation matrices for each sensor and store them in a dictionary
        self.rotation_matrices = {i: self.rotation_matrix_z(self.z_rotations[i]).astype(self.precision) for i in
                                  range(len(self.z_rotations))}

    def get_sensor_rotation(self, sensor_idx):
        # If sensor_idx is 0, no rotation; return identity matrix
        if sensor_idx == 0:
            return np.eye(3, dtype=self.precision)

        elif sensor_idx < len(self.z_rotations):
            # Retrieve the precomputed Z-axis rotation matrix
            rotation_z = self.rotation_matrices[sensor_idx]

            # Combine the fixed X-axis rotation with the Z-axis rotation
            rotation_matrix = np.dot(self.rotation_x, rotation_z)  # Use np.dot for matrix multiplication
            return rotation_matrix
        else:
            raise ValueError("Invalid sensor index")

    def rotation_matrix_x(self, theta):
        """Generates a rotation matrix for a rotation around the X-axis by angle theta."""
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=self.precision)

    def rotation_matrix_z(self, theta):
        """Generates a rotation matrix for a rotation around the Z-axis by angle theta."""
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=self.precision)

    def rotation_matrix_to_euler_angles(self, R):
        """Convert a rotation matrix to Euler angles (alpha, beta, theta)."""
        alpha = np.arctan2(R[2, 1], R[2, 2])  # Yaw (rotation around Z-axis)
        beta = np.arctan2(-R[2, 0], np.sqrt(R[2, 1] ** 2 + R[2, 2] ** 2))  # Pitch (rotation around Y-axis)
        theta = np.arctan2(R[1, 0], R[0, 0])  # Roll (rotation around X-axis)

        # Convert from radians to degrees
        return np.degrees(alpha), np.degrees(beta), np.degrees(theta)

    def test_accuracy(self):
        """Test the accuracy of the rotation matrices."""
        for sensor_idx in range(6):  # Assuming 6 sensors
            rotation_matrix = self.get_sensor_rotation(sensor_idx)
            euler_angles = self.rotation_matrix_to_euler_angles(rotation_matrix)
            print(f"Sensor {sensor_idx} Rotation Matrix:\n", rotation_matrix)
            print(f"Euler Angles (Yaw, Pitch, Roll): {euler_angles}")
            print("---")

    def check_optimization(self):
        """Test optimization performance, checking computation time."""
        import time
        start_time = time.time()
        for sensor_idx in range(10000):  # Test with a large number of iterations
            self.get_sensor_rotation(sensor_idx % 6)  # Only 6 sensor types
        end_time = time.time()
        print(f"Optimization test completed in {end_time - start_time} seconds.")


# Example Usage:
sensor_rotation = OptimizedSensorRotation()

# Check rotation accuracy (Euler angles for all sensors)
sensor_rotation.test_accuracy()

# Check the optimization performance (timing)
sensor_rotation.check_optimization()
