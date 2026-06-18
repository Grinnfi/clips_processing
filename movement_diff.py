import cv2
import numpy as np
from tqdm import tqdm
from crop import crop_polygon

def get_movement(cap, skip_frames, mask_points):
    ret, frame = cap.read()
    if not ret:
        return []
        
    # Get the bounding box metadata and the mask ONE TIME
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, local_mask, x, y, w, h = crop_polygon(gray_frame, mask_points, return_mask_data=True)
    
    mask_volume = np.sum(local_mask)
    if mask_volume == 0:
        mask_volume = 1

    last_roi = gray_frame[y:y+h, x:x+w]
    movement_list = []
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_steps = frame_count // (skip_frames + 1)
    pbar = tqdm(total=total_steps, desc="Processing movement", unit="frame")
    
    while True:
        for _ in range(skip_frames):
            if not cap.grab():
                break
                
        ret, frame = cap.read()
        if not ret:
            break
            
        # Blazing fast C++ matrix slicing using the precalculated coords
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_roi = gray[y:y+h, x:x+w]
        
        # Calculate changes inside the ROI
        diff = cv2.absdiff(current_roi, last_roi)
        _, binary_mask = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)
        
        # Mask out the sky/sea using the local mask
        masked_diff = cv2.bitwise_and(binary_mask, local_mask)
        
        # Pull metric straight out of native memory
        total_diff_sum = cv2.norm(masked_diff, cv2.NORM_L1)
        movement_list.append(int((total_diff_sum / mask_volume) * 100000))
        
        last_roi = current_roi
        pbar.update(1)
        
    pbar.close()
    return movement_list