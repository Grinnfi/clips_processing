import sys
import os
import pickle
import json
from plot import save_plot

import numpy as np

def detect_changes_point(time_series, window_size, threshold):
    """
    Detects abrupt changes in a time series by comparing the window mean to the current value.
    Uses NumPy for calculations and returns integer indices.

    Args:
        time_series (np.ndarray): The input time series as a NumPy array.
        window_size (int): The size of the moving window.
        threshold (float): The maximum allowed percentage change.

    Returns:
        list: A list of integer indices where abrupt changes were detected.
    """
    abrupt_change_indices = []
    
    # Ensure time_series is a NumPy array
    if not isinstance(time_series, np.ndarray):
        time_series = np.asarray(time_series)

    # We start the loop from window_size because we need at least 'window_size'
    # elements before the current element to form the first window.
    for i in range(window_size, len(time_series)):
        current_value = time_series[i]
        
        # Define the window using NumPy slicing
        window = time_series[i - window_size : i]
        window_mean = np.mean(window)

        if current_value == 0 or window_mean == 0:  # Avoid division by zero
            continue # Move to the next iteration

        percentage_change = np.abs((current_value - window_mean) / window_mean)

        if percentage_change > threshold:
            # print(f"id {i}: %: {percentage_change} v: {current_value}  w:{window}")
            abrupt_change_indices.append(i)

    return abrupt_change_indices

def process_ranges(data_path):
    with open (data_path, 'rb') as f:
        data = pickle.load(f)
    with open ("options.json", "r") as f:
        options = json.load(f)

    skip_frames = options["skip_frames"]
    low_threshold = options.get("low_threshold", 0)
    high_threshold = options.get("high_threshold", None)
    change_point_threshold = options.get("change_point_threshold", 0.3)
    window_size = options.get("window_size", 12)
    
    # Ensure data is a NumPy array
    if not isinstance(data, np.ndarray):
        data = np.asarray(data)

    # Find indices where movement is within the threshold limits
    if high_threshold is not None:
        active_indices = np.where((data >= low_threshold) & (data <= high_threshold))[0]
    else:
        active_indices = np.where(data >= low_threshold)[0]
    
    clean_data = []
    if len(active_indices) > 0:
        # Group contiguous active indices, allowing a gap of up to split_gap (e.g., 3 points)
        # This merges close spikes but splits them if there's a longer period of no movement
        split_gap = 3
        start = active_indices[0]
        prev = active_indices[0]
        
        for idx in active_indices[1:]:
            if idx - prev > split_gap:
                clean_data.append((start, prev))
                start = idx
            prev = idx
        clean_data.append((start, prev))

    # Convert to video frame ranges taking skip_frames into account
    frame_ranges = [[int(r[0]*(skip_frames+1)), int(r[1]*(skip_frames+1) + skip_frames)] for r in clean_data]

    processed_folder = os.path.dirname(data_path)
    with open (os.path.join(processed_folder, "ranges.pkl"), "wb") as f:
        pickle.dump(frame_ranges, f)

    print(f"Total ranges = {len(frame_ranges)}")

    save_plot(processed_folder)
    
if __name__ == "__main__":
    data_path = sys.argv[-1]
    process_ranges(data_path)