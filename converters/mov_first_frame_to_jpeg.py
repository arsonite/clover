#!/usr/bin/env python3.11

# Copyright (C) 2024-2026 Burak Günaydin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# Standard-library imports
import sys
from pathlib import Path
from typing import Optional

# Third-party imports
import cv2
from colorama import Fore, Style

# # Local imports
# from .converters.base_converter import BaseConverter

# Used by main.py for automatic converter discovery
CONVERTER_INFO = {
    "name": "MOV First Frame to JPEG",
    "description": "Extract the first frame from MOV videos as JPEG",
    "input_format": "mov",
    "output_format": "jpg",
    "input_category": "video",
    "output_category": "image",
}

# Configuration
JPEG_QUALITY = 95  # 0-100, higher = better quality, larger file

def convert_file(input_path: Path, output_path: Path, quality: int = JPEG_QUALITY) -> tuple[bool, str]:
    """
    Convert a single MOV file to JPEG (first frame).
    
    This is the standardized single-file conversion function called by main.py
    for multithreaded processing.
    
    Args:
        input_path: Path to the input video file
        output_path: Path for the output JPEG file
        quality: JPEG quality (0-100)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        cap = cv2.VideoCapture(str(input_path))
        
        if not cap.isOpened():
            return False, "Cannot open video file"
        
        # Get video info
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            return False, "Cannot read frame"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        success = cv2.imwrite(str(output_path), frame, encode_params)
        
        if not success:
            return False, "Cannot save JPEG"
        
        return True, f"{width}x{height}"
        
    except Exception as e:
        return False, str(e)

def extract_first_frame(video_path: Path, output_path: Path, quality: int = JPEG_QUALITY) -> bool:
    """
    Extract the first frame from a video file and save as JPEG.
    
    Args:
        video_path: Path to the input video file
        output_path: Path for the output JPEG file
        quality: JPEG quality (0-100)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open video capture
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            print(f"{Fore.RED}  ✗ Cannot open: {video_path.name}{Style.RESET_ALL}")
            return False
        
        # Read the first frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            print(f"{Fore.RED}  ✗ Cannot read frame: {video_path.name}{Style.RESET_ALL}")
            return False
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JPEG with specified quality
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        success = cv2.imwrite(str(output_path), frame, encode_params)
        
        if not success:
            print(f"{Fore.RED}  ✗ Cannot save: {output_path.name}{Style.RESET_ALL}")
            return False
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}  ✗ Error processing {video_path.name}: {e}{Style.RESET_ALL}")
        return False

def get_video_info(video_path: Path) -> Optional[dict]:
    """
    Get basic information about a video file.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with video info or None if cannot read
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None
        
        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        }
        cap.release()
        return info
        
    except Exception:
        return None

def convert(input_base: Path, output_base: Path):
    """
    Legacy conversion function for backwards compatibility.
    Called when running converter directly without the new main.py orchestration.
    
    Args:
        input_base: Base input folder path
        output_base: Base output folder path
    """
    from tqdm import tqdm
    
    input_dir = input_base / "video" / "mov"
    output_dir = output_base / "image" / "jpg"
    
    print(f"{Fore.WHITE}=== MOV First Frame to JPEG Converter ==={Style.RESET_ALL}\n")
    print(f"  Input folder:  {Fore.CYAN}{input_dir}{Style.RESET_ALL}")
    print(f"  Output folder: {Fore.CYAN}{output_dir}{Style.RESET_ALL}")
    print()
    
    if not input_dir.exists():
        print(f"{Fore.YELLOW}Input directory does not exist. Creating it...{Style.RESET_ALL}")
        input_dir.mkdir(parents=True, exist_ok=True)
        print(f"{Fore.CYAN}Place your .mov files in: {input_dir}{Style.RESET_ALL}")
        return
    
    mov_files = list(input_dir.glob("*.mov")) + list(input_dir.glob("*.MOV"))
    
    if not mov_files:
        print(f"{Fore.YELLOW}No .mov files found in {input_dir}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Place your .mov files there and run again.{Style.RESET_ALL}")
        return
    
    print(f"Found {Fore.GREEN}{len(mov_files)}{Style.RESET_ALL} .mov file(s)\n")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    for mov_file in tqdm(mov_files, desc="Converting", unit="file"):
        output_file = output_dir / (mov_file.stem + ".jpg")
        success, info = convert_file(mov_file, output_file)
        
        if success:
            tqdm.write(f"  {Fore.GREEN}✓{Style.RESET_ALL} {mov_file.name} [{info}] → {output_file.name}")
            success_count += 1
        else:
            tqdm.write(f"  {Fore.RED}✗{Style.RESET_ALL} {mov_file.name}: {info}")
            fail_count += 1
    
    print(f"\n{Fore.WHITE}=== Conversion Complete ==={Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Successful: {success_count}{Style.RESET_ALL}")
    if fail_count > 0:
        print(f"  {Fore.RED}Failed: {fail_count}{Style.RESET_ALL}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_base_path> <output_base_path>")
        sys.exit(1)
    
    convert(Path(sys.argv[1]).expanduser().resolve(),
            Path(sys.argv[2]).expanduser().resolve())