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
from pathlib import Path

# Third-party imports
from pillow_heif import register_heif_opener
from PIL import Image

# Local imports
from .base_converter import BaseConverter

# Register HEIF opener with Pillow
register_heif_opener()

class HeicToJpegConverter(BaseConverter):
    name='(Apple) HEIC to JPEG'
    description='Convert HEIC/HEIF images to JPEG format'
    includes_proprietary_formats=True # HEIC relies on patented technology
    input_category='image'
    input_format='heic'
    output_format='jpg'
    output_category='image'
    
    def convert(self, input_data, output_data):
        pass
    
    def convert_file(self,
                     input_path:Path,
                     output_path:Path,
                     quality:int=95) -> tuple[bool, str]:
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
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Get image info for message
                width, height = img.size
                
                # Save as JPEG
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            return True, f'{width}x{height}'
        except Exception as e:
            return False, str(e)