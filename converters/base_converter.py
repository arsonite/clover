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
from abc import ABC, abstractmethod

class BaseConverter(ABC):
    """
    Abstract base class for all converters.
    
    Defines the interface that all converter modules must implement.
    """
    converter_category:str            # e.g. "image", "video", "audio"
    converter_info:str                # auxilliary info like a short description or special notes
    from_type:str                     # e.g. "heic", "mov"
    includes_proprietary_formats:bool # True if the converter relies on proprietary formats or libraries
    to_type:str                       # e.g. "jpg", "mp4"
    
    @abstractmethod
    def convert_file(self, input_path:str, output_path:str) -> tuple[bool,str]:
        """
        Convert a single file from input_path to output_path.
        
        Args:
            input_path: Path to the input file
            output_path: Path for the output file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        raise NotImplementedError('convert_file method must be implemented by subclasses')
