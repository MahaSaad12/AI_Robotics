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

        # Add ground truth (define per your test setup)
        expected_visible_faces = {
            0: [0, 1, 5],
            1: [2, 3, 4],
            2: [6, 7, 8],
            3: [9, 10, 11],
            4: [12, 13, 14],
            5: [15, 16, 17]
        }

        distances = []
        angles = []
        visible_faces = []
        orientations = []
        sensor_status = []
        sensor_indices = []
        visibility_scores = []

        for sensor_idx, sensor_position in enumerate(sensor_positions):
            rotation_matrix, visible_count, face_data = self.get_sensor_rotation(sensor_idx)
            if rotation_matrix is None:
                rotation_matrix = np.eye(3)

            sensor_color = self.unique_sensor_colors[sensor_idx % len(self.unique_sensor_colors)]

            alpha, beta, theta = self.rotation_matrix_to_euler_angles(rotation_matrix)
            orientations.append((alpha, beta, theta))

            actual_faces = set(face_idx for face_idx, *_ in face_data)
            expected_faces = set(expected_visible_faces.get(sensor_idx, []))
            score = len(actual_faces & expected_faces) / max(len(expected_faces), 1)
            visibility_scores.append(f"{score:.2f}")
            status = "GOOD" if visible_count >= 5 else "BAD"
            sensor_status.append(status)

            if actual_faces != expected_faces:
                print(f"[Sensor {sensor_idx}] MISMATCH:")
                print(f"  Expected: {sorted(expected_faces)}")
                print(f"  Actual:   {sorted(actual_faces)}\n")

            for face_idx, distance, angle, face_center in face_data:
                face_vertices = vertices[faces[face_idx]]
                poly = Poly3DCollection([face_vertices], alpha=0.4, edgecolor="black")
                self.ax.add_collection3d(poly)

                self.draw_view_frustum(sensor_position, face_center, fov, sensor_color)
                connection_lines.append([sensor_position, face_center])

                face_normal = self.calculate_face_normal(face_vertices)
                self.draw_face_normal(face_center, face_normal)

                deviation = self.calculate_angle((face_center - sensor_position) / np.linalg.norm(face_center - sensor_position), face_normal)
                print(f"Sensor {sensor_idx} → Face {face_idx}: Angle = {angle:.2f}°, Deviation = {deviation:.2f}°, Dist = {distance:.2f}")

                visible_faces.append(face_idx)
                distances.append(distance)
                angles.append(angle)
                sensor_indices.append(sensor_idx)

            avg_angle = np.mean([angle for _, _, angle, _ in face_data])
            avg_distance = np.mean([distance for _, distance, _, _ in face_data])
            print(f"\n[Sensor {sensor_idx}] {len(face_data)} visible faces | Avg Angle: {avg_angle:.2f}° | Avg Dist: {avg_distance:.2f}\n")

            self.ax.scatter(*sensor_position, color=sensor_color, label=f"Sensor {sensor_idx + 1}", s=80)

        connection_colors = plt.cm.viridis(np.linspace(0, 1, len(connection_lines)))
        line_collection = Line3DCollection(connection_lines, colors=connection_colors, linewidths=1.5, alpha=0.8)
        self.ax.add_collection3d(line_collection)

        self.ax.set_xlabel("X-axis", fontsize=12)
        self.ax.set_ylabel("Y-axis", fontsize=12)
        self.ax.set_zlabel("Z-axis", fontsize=12)
        self.ax.legend(fontsize=10)

        self.update_table(distances, angles, visible_faces, orientations, sensor_status, sensor_indices, visibility_scores)
        self.draw_idle()
    except Exception as e:
        print("Error during update_scene:", e)
    finally:
        self._updating = False
