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
import cv2

# Local imports
from .base_converter import BaseConverter

# Configuration
JPEG_QUALITY = 95  # 0-100, higher = better quality, larger file

class MovFirstFrameToJpegConverter(BaseConverter):
    name="MOV First Frame to JPEG"
    description="Extract the first frame from MOV videos as JPEG"
    includes_proprietary_formats=False
    input_category='video'
    input_format='mov'
    output_format='jpg'
    output_category='image'
    
    def convert(self, input_data, output_data, quality=JPEG_QUALITY):
        """
        Convert a single MOV file to JPEG (first frame).
        
        Args:
            input_data: Path to the input video file
            output_data: Path for the output JPEG file
            quality: JPEG quality (0-100)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        return self.convert_file(input_data, output_data, quality=quality)
    
    def convert_file(self,
                     input_path:Path,
                     output_path:Path,
                     *,
                     quality:int=JPEG_QUALITY) -> tuple[bool,str]:
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
                return False, 'Cannot open video file'
            
            # Get video info
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                return False, 'Cannot read frame'
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success = cv2.imwrite(str(output_path), frame, encode_params)
            
            if not success:
                return False, 'Cannot save JPEG'
            
            return True, f'{width}x{height}'
            
        except Exception as e:
            return False, str(e)