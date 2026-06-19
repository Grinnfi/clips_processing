import cv2
import json
import os
import sys
import pickle

from create_processed_folder import create_processed_folder
from save_frames import save_frames


WINDOW_NAME = 'Frame'

def load_progress(save_path):
    with open(save_path, 'r') as f:
        try:
            progress = json.load(f)
            return progress.get('frame_ranges'), progress.get('validated_ranges'), progress.get('current_range_index'), progress.get('complet')
        except json.JSONDecodeError:
            print("Error decoding save file. Starting fresh.")
            return 1

def save_progress(save_path, frame_ranges, validated_ranges, current_range_index, complet = False):
    progress = {'frame_ranges': frame_ranges, 'validated_ranges': validated_ranges, 'current_range_index': current_range_index, 'complet':complet}
    with open(save_path, 'w') as f:
        json.dump(progress, f)
    print(f"💾 Progress saved to {save_path}")


def validate_ranges(video_path):
    cap = cv2.VideoCapture(video_path)

    processed_path = create_processed_folder(video_path)
    save_path = os.path.join(processed_path, "video_review_progress.json")

    with open(os.path.join(processed_path, "ranges.pkl"), "rb") as f:
        frame_ranges = pickle.load(f)

    validated_ranges = []
    current_range_index = 0
    
    if os.path.exists(save_path):
        answer = input("Load previous progress? (y/n): ").lower()
        if answer == 'y':
            frame_ranges, validated_ranges, current_range_index, complet = load_progress(save_path)
            print("Loaded previous progress.")
            if complet == True:
                print("Loaded file is already complet!")
                return 0
        else:
            print("Starting fresh.")
    else:
        print("No previous progress found. Starting fresh.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # fps = cap.get(cv2.CAP_PROP_FPS)

    speed = 8 # Milliseconds between frames in auto mode
    manual_step = 1
    manual_step_large = 20
    review_mode = "auto"  # Can be "auto" or "manual"
    early_exit = False

    while current_range_index < len(frame_ranges) and not early_exit:
        start, end = frame_ranges[current_range_index]

        # Validate bounds
        if start < 0 or end >= total_frames or start >= end:
            print(f"Invalid range: [{start}, {end}]")
            current_range_index += 1
            continue

        print(f"Reviewing range: [{start}, {end}] - ", end="")
        if review_mode == "auto":
            print("Press UP to validate, DOWN to skip, LEFT/RIGHT to step (manual), SPACE to pause (manual), ESC to exit.")
        elif review_mode == "manual":
            print("Press UP to validate until current frame, DOWN to skip until current frame, LEFT/RIGHT to step, SPACE to resume (auto), ESC to exit.")

        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        current_frame = start
        range_length = end - start + 1

        # Create a resizable window
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

        while True:
            if current_frame > end and review_mode == "auto":
                current_frame = start
                cap.set(cv2.CAP_PROP_POS_FRAMES, start)
            # elif current_frame < start and review_mode == "manual":
            #     current_frame = start
            #     cap.set(cv2.CAP_PROP_POS_FRAMES, start)

            ret, frame = cap.read()
            if not ret:
                break

            # Calculate relative frame number
            relative_pos = current_frame - start + 1
            overlay_text = f"{relative_pos}/{range_length}   {current_frame}"

            # Put the overlay on the frame
            cv2.putText(frame, overlay_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('Frame', frame)

            key_code = cv2.waitKeyEx(speed if review_mode == "auto" else 0)
            key_ascii = key_code & 0xFF if key_code != -1 else -1
            # print(f"Key pressed: {key_code} (ASCII: {key_ascii})")  # Debug print for key codes

            # Define arrow key codes (handling standard waitKeyEx and platform specific keysyms)
            LEFT_KEYS = [2424832, 0x250000, 65361]
            RIGHT_KEYS = [2555904, 0x270000, 65363]
            UP_KEYS = [2490368, 0x260000, 65362]
            DOWN_KEYS = [2621440, 0x280000, 65364]
            # Page up/down and Home/End keys (several platform variants)
            PAGE_UP_KEYS = [2162688, 0x210000, 65365]
            PAGE_DOWN_KEYS = [2228224, 0x220000, 65366]
            HOME_KEYS = [2359296, 0x240000, 65360]
            END_KEYS = [2293760, 0x2b0000, 65367]

            # Determine adjacent-range clamps for stepping/jumping
            prev_end = frame_ranges[current_range_index - 1][1] if current_range_index > 0 else 0
            next_start = frame_ranges[current_range_index + 1][0] if current_range_index < len(frame_ranges) - 1 else total_frames - 1
            # Allow stepping to at most the previous range end (min) and next range start (max)
            step_min = prev_end
            step_max = next_start

            if key_code in UP_KEYS:
                if review_mode == "manual" and current_frame < end:
                    actual_start = min(start, current_frame)
                    actual_end = max(start, current_frame)
                    
                    validated_ranges.append([actual_start, actual_end])
                    print(f"✅ Validated split range: [{actual_start}, {actual_end}]")
                    
                    # Move the next start point safely to the frame right after our max boundary
                    start = actual_end + 1
                    frame_ranges[current_range_index] = [start, end]
                    current_frame = start
                    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
                    range_length = end - start + 1
                    review_mode = "auto"
                    print("Switched to auto review mode.")
                else:
                    validated_ranges.append([start, end])
                    print(f"✅ Validated range: [{start}, {end}]")
                    break
            elif key_code in DOWN_KEYS:
                if review_mode == "manual" and current_frame < end:
                    actual_start = min(start, current_frame)
                    actual_end = max(start, current_frame)
                    
                    print(f"❌ Skipped split range: [{actual_start}, {actual_end}]")
                    
                    start = actual_end + 1
                    frame_ranges[current_range_index] = [start, end]
                    current_frame = start
                    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
                    range_length = end - start + 1
                    review_mode = "auto"
                    print("Switched to auto review mode.")
                else:
                    print(f"❌ Skipped range: [{start}, {end}]")
                    break
            elif key_code in LEFT_KEYS:
                if review_mode == "auto":
                    review_mode = "manual"
                # Step backward
                current_frame = max(step_min, current_frame - manual_step)
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            elif key_code in RIGHT_KEYS:
                if review_mode == "auto":
                    review_mode = "manual"
                # Step forward
                current_frame = min(step_max, current_frame + manual_step)
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            elif key_code in PAGE_UP_KEYS:
                # Jump forward
                if review_mode == "auto":
                    review_mode = "manual"
                current_frame = min(step_max, current_frame + manual_step_large)
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            elif key_code in PAGE_DOWN_KEYS:
                # Jump backward
                if review_mode == "auto":
                    review_mode = "manual"
                current_frame = max(step_min, current_frame - manual_step_large)
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            elif key_code in HOME_KEYS:
                # Go to start of the current range
                if review_mode == "auto":
                    review_mode = "manual"
                current_frame = start
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            elif key_code in END_KEYS:
                # Go to end of the current range
                if review_mode == "auto":
                    review_mode = "manual"
                current_frame = end
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            elif key_ascii == 27:  # ESC key
                early_exit = True
                save_progress(save_path, frame_ranges, validated_ranges, current_range_index)
                break
            elif key_ascii == ord(' '):  # Space
                review_mode = "auto" if review_mode == "manual" else "manual"
                print(f"Switched to {review_mode} review mode.")
            elif review_mode == "auto":
                current_frame += 1

        if early_exit:
            print("🚪 Exiting early due to ESC key.")
            break

        current_range_index += 1

    cap.release()
    cv2.destroyAllWindows()

    if current_range_index == len(frame_ranges):
        save_progress(save_path, frame_ranges, validated_ranges, current_range_index, True)
        print("🎉 All work is done!")
        save = input("Save now? y/n: ")
        if save == "y":
            save_frames(video_path)

    # print("\nValidated Ranges:", validated_ranges)
    # print("Total Ranges:", frame_ranges)

if __name__ == "__main__":
    video_path = sys.argv[-1]
    validate_ranges(video_path)
