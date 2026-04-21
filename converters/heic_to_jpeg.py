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
from colorama import Fore, Style
from pillow_heif import register_heif_opener
from PIL import Image

# Register HEIF opener with Pillow
register_heif_opener()

# Used by main.py for automatic converter discovery
CONVERTER_INFO = {
    "name": "HEIC to JPEG",
    "description": "Convert HEIC/HEIF images to JPEG format",
    "input_format": "heic",
    "output_format": "jpg",
    "input_category": "image",
    "output_category": "image",
}

# Configuration
JPEG_QUALITY = 95  # 0-100, higher = better quality

def convert_file(input_path: Path, output_path: Path, quality: int = JPEG_QUALITY) -> tuple[bool, str]:
    """
    Convert a single HEIC file to JPEG.
    
    This is the standardized single-file conversion function called by main.py
    for multithreaded processing.
    
    Args:
        input_path: Path to the input HEIC file
        output_path: Path for the output JPEG file
        quality: JPEG quality (0-100)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open HEIC image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (HEIC can have alpha channel)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Get image info for message
            width, height = img.size
            
            # Save as JPEG
            img.save(output_path, "JPEG", quality=quality, optimize=True)
        
        return True, f"{width}x{height}"
        
    except Exception as e:
        return False, str(e)

def get_file_info(file_path: Path) -> Optional[dict]:
    """
    Get information about a HEIC file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file info or None if cannot read
    """
    try:
        with Image.open(file_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
            }
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
    
    input_dir = input_base / "image" / "heic"
    output_dir = output_base / "image" / "jpg"
    
    print(f"{Fore.WHITE}=== HEIC to JPEG Converter ==={Style.RESET_ALL}\n")
    print(f"  Input folder:  {Fore.CYAN}{input_dir}{Style.RESET_ALL}")
    print(f"  Output folder: {Fore.CYAN}{output_dir}{Style.RESET_ALL}")
    print()
    
    if not input_dir.exists():
        print(f"{Fore.YELLOW}Input directory does not exist. Creating it...{Style.RESET_ALL}")
        input_dir.mkdir(parents=True, exist_ok=True)
        print(f"{Fore.CYAN}Place your .heic files in: {input_dir}{Style.RESET_ALL}")
        return
    
    # Find all HEIC files (case insensitive)
    heic_files = list(input_dir.glob("*.heic")) + list(input_dir.glob("*.HEIC"))
    heic_files += list(input_dir.glob("*.heif")) + list(input_dir.glob("*.HEIF"))
    
    if not heic_files:
        print(f"{Fore.YELLOW}No .heic/.heif files found in {input_dir}{Style.RESET_ALL}")
        return
    
    print(f"Found {Fore.GREEN}{len(heic_files)}{Style.RESET_ALL} HEIC file(s)\n")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    for heic_file in tqdm(heic_files, desc="Converting", unit="file"):
        output_file = output_dir / (heic_file.stem + ".jpg")
        success, info = convert_file(heic_file, output_file)
        
        if success:
            tqdm.write(f"  {Fore.GREEN}✓{Style.RESET_ALL} {heic_file.name} [{info}] → {output_file.name}")
            success_count += 1
        else:
            tqdm.write(f"  {Fore.RED}✗{Style.RESET_ALL} {heic_file.name}: {info}")
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