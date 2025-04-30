import numpy as np

class SensorRotation:
    ##by checking the unit vector
    ## check by assumping all the x,y,z plane shoulde be 0 if the answer is [1.0.0] done with correctness of roatation matrics
    def __init__(self):
        """Precompute rotation_x since it is constant for all sensors"""
        self.rotation_x = self.rotation_matrix_x(0)

        # Precompute rotation matrices for Z-axis rotations
        self.z_rotations = {i: self.rotation_matrix_z(angle) for i, angle in enumerate([0, 0, 0, 0, 0, 0])}

    def get_sensor_rotation(self, sensor_idx):
        """Fetch precomputed rotation matrices instead of recalculating them"""
        rotation_z = self.z_rotations.get(sensor_idx, np.eye(3))  # Get precomputed Z rotation
        return np.dot(self.rotation_x, rotation_z)

    def rotation_matrix_x(self, theta):
        """Generate a rotation matrix around the X-axis"""
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

    def rotation_matrix_z(self, theta):
        """Generate a rotation matrix around the Z-axis"""
        c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    def test_rotation_matrix(self, sensor_idx):
        """Test if rotation matrix correctly transforms a unit vector"""
        rotation_matrix = self.get_sensor_rotation(sensor_idx)

        # Apply the rotation to a unit vector along X-axis
        unit_vector = np.array([1, 0, 0])
        transformed_vector = np.dot(rotation_matrix, unit_vector)

        print(f"Sensor {sensor_idx} - Transformed Vector: {transformed_vector}")

# Example Usage:
sensor_rotation = SensorRotation()
sensor_rotation.test_rotation_matrix(0)  # Check for sensor 0
sensor_rotation.test_rotation_matrix(1)  # Check for sensor 1
