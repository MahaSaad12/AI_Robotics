import pandas as pd

# Define expected faces for each sensor (your ground truth)
expected_visible_faces = {
    "Sensor 1": [0, 1, 5],
    "Sensor 2": [3, 4, 10],
    "Sensor 3": [6, 7, 8],
    "Sensor 4": [9, 10, 11],
    "Sensor 5": [12, 13, 14],
    "Sensor 6": [15, 16, 17]
}

# Load the CSV
df = pd.read_csv("sensor_distance.csv")

# Remove 'Index' column if it exists
if "Index" in df.columns:
    df.drop(columns=["Index"], inplace=True)

print("=== Distance-Based Visibility Report ===\n")

# Loop through each sensor column
for sensor in df.columns:
    distances = df[sensor].astype(float)

    # Simulate detected "face" indices by taking the index of min distance in each row
    detected_faces = set(distances.nsmallest(3).index)  # smallest 3 distances as detected faces
    expected_faces = set(expected_visible_faces.get(sensor, []))
    matched = detected_faces & expected_faces

    accuracy = len(matched) / max(len(expected_faces), 1)
    avg_distance = distances.mean()

    print(f"{sensor}:")
    print(f"  ✅ Detected Face Indices : {sorted(detected_faces)}")
    print(f"  🎯 Expected Faces         : {sorted(expected_faces)}")
    print(f"  🎯 Correct Matches        : {sorted(matched)}")
    print(f"  📈 Accuracy Score         : {accuracy:.2f}")
    print(f"  📏 Avg Distance           : {avg_distance:.2f}\n")
