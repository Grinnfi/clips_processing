import os
import cv2
import json
import pickle
import argparse

from create_processed_folder import create_processed_folder


def merge_ranges(frame_ranges):
    # Merge if end[n] = start[n+1]
    new_frame_ranges = [frame_ranges[0]]
    for frame_range in frame_ranges[1:]:
        if frame_range[0] <= new_frame_ranges[-1][1] + 1:
            new_frame_ranges[-1][1] = frame_range[1]
        else:
            new_frame_ranges.append(frame_range)
    return new_frame_ranges


def get_crop_coords(folder_path):
    points_path = os.path.join(folder_path, "points.pkl")
    with open(points_path, "rb") as f:
        points = pickle.load(f)
    
    x_coords = [point[0] for point in points]
    y_coords = [point[1] for point in points]
    x_min = min(x_coords)
    x_max = max(x_coords)
    y_min = min(y_coords)
    y_max = max(y_coords)
    return x_min, x_max, y_min, y_max


def save_frames(video_path, crop=False, start_frame=None, end_frame=None, skip_frames_save=None, output_path=None):
    processed_folder = create_processed_folder(video_path, output_path=output_path)
    review_path = os.path.join(processed_folder, "video_review_progress.json")
    save_folder = os.path.join(processed_folder, "frames")
    
    if not os.path.exists(save_folder):
        print(f"Creating directory {save_folder}")
        os.mkdir(save_folder)

    with open(review_path, "r") as f:
        frame_ranges = json.load(f)["validated_ranges"]

    frame_ranges = merge_ranges(frame_ranges)

    # Filter or clip frame ranges if custom start_frame or end_frame are specified
    if start_frame is not None or end_frame is not None:
        filtered_ranges = []
        for r_start, r_end in frame_ranges:
            s = start_frame if start_frame is not None else r_start
            e = end_frame if end_frame is not None else r_end
            if s <= e and not (r_end < s or r_start > e):
                filtered_ranges.append([max(s, r_start), min(e, r_end)])
        frame_ranges = filtered_ranges

    if crop:
        x_min, x_max, y_min, y_max = get_crop_coords(processed_folder)

    # Use argument if provided, otherwise fallback to options.json
    if skip_frames_save is None:
        if os.path.exists("options.json"):
            with open("options.json", "r") as f:
                skip_frames_save = json.load(f).get("skip_frames_save", 1)
        else:
            skip_frames_save = 1

    cap = cv2.VideoCapture(video_path)
    saved_count = 0

    for frame_range in frame_ranges:
        current_frame_index = frame_range[0]
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)

        for current_frame_index in range(frame_range[0], frame_range[1], skip_frames_save):
            _, frame = cap.read()
            if frame is None:
                break
            if crop:
                frame = frame[y_min:y_max, x_min:x_max]  # Crop
            cv2.imwrite(os.path.join(save_folder, f"{current_frame_index}.jpg"), frame)
            saved_count += 1
            
            for _ in range(skip_frames_save):  # Skip frames without decoding
                cap.grab() # Faster than set in small gaps, faster than read when not decoding

    print(f"Total frames saved: {saved_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save processed video frames.")
    parser.add_argument("video_path", type=str, help="Path to the video file")
    parser.add_argument("--output_path", nargs="?", default=None, help="Optional output path or directory name")
    parser.add_argument("--start-frame", type=int, default=None, help="Optional start frame limit")
    parser.add_argument("--end-frame", type=int, default=None, help="Optional end frame limit")
    parser.add_argument("--skip-frames", dest="skip_frames_save", type=int, default=None, help="Optional skip frames step")
    parser.add_argument("--crop", action="store_true", help="Whether to crop the frames")

    args = parser.parse_args()

    save_frames(
        video_path=args.video_path,
        crop=args.crop,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        skip_frames_save=args.skip_frames_save,
        output_path=args.output_path
    )