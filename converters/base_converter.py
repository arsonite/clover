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
from typing import Optional

class BaseConverter(ABC):
    """
    Abstract base class for all converters.
    
    Defines the interface that all converter modules must implement.
    """
    name:str                          # Human-readable name of the converter  
    description:str                   # Short description of what the converter does
    includes_proprietary_formats:bool # True if the converter relies on proprietary formats or libraries
    input_category:str                # e.g. "image", "video", "audio"
    input_format:str                  # e.g. "heic", "mov"
    output_format:str                 # e.g. "jpg", "mp4"
    output_category:str               # e.g. "image", "video", "audio"
    
    @abstractmethod
    def convert(self, input_data:any, output_data:any, **kwargs) -> tuple[bool,str]:
        """
        Convert input_data to output_data.
        
        This is the main conversion function that can be called by main.py for single-threaded processing.
        It can also be called by convert_file for multithreaded processing.
        It's for use in-memory.
        
        Args:
            input_data: Path or data for the input file
            output_data: Path or data for the output file
            kwargs: Additional keyword arguments (e.g. quality)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        raise NotImplementedError('convert method must be implemented by subclasses')
    
    @abstractmethod
    def convert_file(self,
                     input_path:str,
                     output_path:str,
                     **kwargs) -> tuple[bool,str]:
        """
        Convert a single file from input_path to output_path.
        
        Args:
            input_path: Path to the input file
            output_path: Path for the output file
            quality: Optional quality parameter (e.g. for JPEG compression)
            
        Returns:
            Tuple of (success:bool, message:str)
        """
        raise NotImplementedError('convert_file method must be implemented by subclasses')
