import cv2
import numpy as np
from tqdm import tqdm
from crop import crop_polygon

def get_movement(cap, skip_frames, mask_points, method="absdiff"):
    """
    Calculates movement metric within a ROI.
    
    Parameters:
        cap: cv2.VideoCapture instance
        skip_frames (int): Number of frames to skip between calculations
        mask_points: Polygon points for ROI
        method (str): Algorithm to use -> 'absdiff' (default) or 'mog2'
    """
    ret, frame = cap.read()
    if not ret:
        return []
        
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, local_mask, x, y, w, h = crop_polygon(gray_frame, mask_points, return_mask_data=True)
    
    mask_volume = np.sum(local_mask)
    if mask_volume == 0:
        mask_volume = 1

    last_roi = gray_frame[y:y+h, x:x+w]
    movement_list = []
    
    # Initialize algorithm-specific state
    if method == "mog2":
        back_sub = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=36, detectShadows=False
        )
    elif method == "absdiff":
        pass
    else:
        raise ValueError(f"Unknown movement method: '{method}'. Choose 'absdiff' or 'mog2'.")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_steps = frame_count // (skip_frames + 1)
    pbar = tqdm(total=total_steps, desc=f"Processing movement ({method})", unit="frame")
    
    while True:
        for _ in range(skip_frames):
            if not cap.grab():
                break
                
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_roi = gray[y:y+h, x:x+w]
        
        # Calculate change binary mask based on selected method
        if method == "absdiff":
            diff = cv2.absdiff(current_roi, last_roi)
            _, binary_mask = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)
            last_roi = current_roi
        elif method == "mog2":
            binary_mask = back_sub.apply(current_roi)

        # Apply polygon mask
        masked_diff = cv2.bitwise_and(binary_mask, local_mask)
        
        # Calculate density metric
        total_diff_sum = cv2.norm(masked_diff, cv2.NORM_L1)
        movement_list.append(int((total_diff_sum / mask_volume) * 100_000))
        
        pbar.update(1)
        
    pbar.close()
    return movement_list