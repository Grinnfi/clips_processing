import os
import sys
import cv2
import json
import pickle

from create_processed_folder import create_processed_folder


def merge_ranges(frame_ranges):
    # Merge if end[n] = start[n+1]
    new_frame_ranges = [frame_ranges[0]]
    for frame_range in frame_ranges[1:]:
        if frame_range[0] <= new_frame_ranges[-1][1] +1:
            new_frame_ranges[-1][1] = frame_range[1]
        else:
            new_frame_ranges.append(frame_range)
    return new_frame_ranges


def get_crop_coords(folder_path):
    points_path = os.path.join(folder_path, "points.pkl")
    with open(points_path, "rb") as f:
        points = pickle.load(f)
    x_coords, y_coords = zip(*points)

    x_coords = [point[0] for point in points]
    y_coords = [point[1] for point in points]
    x_min = min(x_coords)
    x_max = max(x_coords)
    y_min = min(y_coords)
    y_max = max(y_coords)
    return x_min, x_max, y_min, y_max

def save_frames(video_path, crop=False, output_path=None):
    processed_folder = create_processed_folder(video_path, output_path=output_path)
    review_path = os.path.join(processed_folder, "video_review_progress.json")
    save_folder = os.path.join(processed_folder, "frames")
    if not os.path.exists(save_folder):
        print(f'Criando diretório {save_folder}')
        os.mkdir(save_folder)

    with open(review_path, "r") as f:
        frame_ranges = json.load(f)["validated_ranges"]

    frame_ranges = merge_ranges(frame_ranges)

    if crop:
        x_min, x_max, y_min, y_max = get_crop_coords(processed_folder)

    with open("options.json", "r") as f:
        skip_frames_save = json.load(f)["skip_frames_save"]

    cap = cv2.VideoCapture(video_path)
    for frame_range in frame_ranges:
        current_frame_index = frame_range[0]
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)

        for current_frame_index in range(frame_range[0], frame_range[1], skip_frames_save):
            _, frame = cap.read()
            if crop:
                frame = frame[y_min:y_max, x_min:x_max] # Crop
            cv2.imwrite(os.path.join(save_folder, f"{current_frame_index}.jpg"), frame)
            for _ in range(skip_frames_save): # Skip frames without decoding
                cap.grab() # Faster than set in small gaps, faster than read when not decoding


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Save processed video frames.")
    parser.add_argument("video_path", help="Path to input video file")
    parser.add_argument("output_path", nargs="?", default=None, help="Optional output path or directory name")
    parser.add_argument("--crop", action="store_true", help="Crop saved frames using ROI points")
    args = parser.parse_args()

    save_frames(args.video_path, crop=args.crop, output_path=args.output_path)