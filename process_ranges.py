import sys
import os
import pickle
import json
from plot import save_plot

import numpy as np

def process_ranges(data_path):
    with open (data_path, 'rb') as f:
        data = pickle.load(f)
    with open ("options.json", "r") as f:
        options = json.load(f)

    skip_frames = options.get("skip_frames")
    low_threshold = options.get("low_threshold", 0)
    high_threshold = options.get("high_threshold", None)
    min_group_size = options.get("min_group_size", 10) 

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
        # Step 1: Find completely raw, contiguous blocks (no split_gap applied yet)
        raw_groups = []
        start = active_indices[0]
        prev = active_indices[0]
        
        for idx in active_indices[1:]:
            if idx - prev > 1:  # Strict contiguity
                raw_groups.append([start, prev])
                start = idx
            prev = idx
        raw_groups.append([start, prev])
        
        # Step 2: Conditionally merge small groups across a split_gap
        split_gap = 3
        merged_groups = []
        
        i = 0
        while i < len(raw_groups):
            curr_start, curr_end = raw_groups[i]
            curr_size = curr_end - curr_start + 1
            
            # If this group is already large enough, keep it independently
            if curr_size >= min_group_size:
                merged_groups.append((curr_start, curr_end))
                i += 1
                continue
            
            # If it's too small, look ahead to see if we can bridge gaps to save it
            while i < len(raw_groups) - 1:
                next_start, next_end = raw_groups[i + 1]
                gap = next_start - curr_end
                
                # Can we bridge the gap to the next group?
                if gap <= split_gap:
                    curr_end = next_end  # Merge them
                    curr_size = curr_end - curr_start + 1
                    i += 1
                    
                    # If the combined group now passes the threshold, stop merging
                    if curr_size >= min_group_size:
                        break
                else:
                    # Next group is too far away to merge
                    break
            
            # Only keep the final merged group if it successfully passed the min check
            if curr_size >= min_group_size:
                merged_groups.append((curr_start, curr_end))
                
            i += 1
            
        clean_data = merged_groups

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