from process_movement import process_movement
from process_ranges import process_ranges
from validate_ranges import validate_ranges
import sys

def process_clip(clip_path, output_path=None):
    print("Processing Movement.")
    movement_path = process_movement(clip_path, output_path=output_path)
    print("Processing Ranges.")
    process_ranges(movement_path)
    validate = input("Validate clip now? (y/n): ").lower()
    if validate == "y":
        validate_ranges(clip_path, output_path=output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process video clip.")
    parser.add_argument("clip_path", help="Path to input video clip")
    parser.add_argument("output_path", nargs="?", default=None, help="Optional output path or directory name")
    args = parser.parse_args()

    process_clip(args.clip_path, output_path=args.output_path)