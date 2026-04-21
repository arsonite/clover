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
import importlib.util
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Third-party imports
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize colorama for cross-platform colored output
init()

# === FOLDER STRUCTURE CONFIGURATION ===
INPUT_SUBFOLDERS = {
    "video": [
        "mov",
        # "mp4",
        # "avi",
        # "mkv",
        # "webm",
        # "flv",
        # "wmv",
        # "m4v"
    ],
    "image": [
        "jpg",
        "jpeg",
        "png",
        # "gif",
        # "bmp",
        # "tiff",
        # "webp",
        "heic",
        # "raw"
    ],
    # "audio": [
    #     "mp3",
    #     "wav",
    #     "flac",
    #     "ogg",
    #     "aac",
    #     "m4a",
    #     "wma",
    #     "aiff"
    # ],
}

OUTPUT_SUBFOLDERS = {
    # "video": [
    #     "mp4",
    #     "webm",
    #     "avi",
    #     "mkv",
    #     "gif"
    # ],
    "image": [
        "jpg",
        "png",
        # "webp",
        # "gif",
        # "bmp",
        # "tiff"
    ],
    # "audio": [
    #     "mp3",
    #     "wav",
    #     "flac",
    #     "ogg",
    #     "aac"
    # ],
}

# Default number of worker threads
DEFAULT_WORKERS = 4

@dataclass
class ConverterInfo:
    """Information about a converter module."""
    name: str
    description: str
    input_format: str
    output_format: str
    input_category: str
    output_category: str
    module_path: Path
    module: object = None

def print_banner():
    """
    Print the application banner.
    """
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                           {Fore.WHITE}C L O V E R{Fore.CYAN}                        ║
║                   {Fore.YELLOW}Video • Image • Audio Converter{Fore.CYAN}            ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def get_folder_path(prompt:str, must_exist:bool=False) -> Path:
    """
    Prompt user for a folder path.
    """
    while True:
        path_str = input(f"{Fore.GREEN}{prompt}{Style.RESET_ALL} ").strip()
        
        if not path_str:
            print(f"{Fore.RED}Error: Path cannot be empty{Style.RESET_ALL}")
            continue
        
        path = Path(path_str).expanduser().resolve()
        
        if must_exist and not path.exists():
            print(f"{Fore.RED}Error: Path does not exist: {path}{Style.RESET_ALL}")
            continue
        return path

def create_folder_structure(base_path:Path, subfolders:dict, folder_type:str) -> dict:
    """
    Create the folder structure for input or output.
    """
    format_paths = {}
    
    print(f"\n{Fore.YELLOW}Creating {folder_type} folder structure in: {base_path}{Style.RESET_ALL}")
    
    base_path.mkdir(parents=True, exist_ok=True)
    
    for category, formats in subfolders.items():
        category_path = base_path / category
        category_path.mkdir(exist_ok=True)
        
        for fmt in formats:
            fmt_path = category_path / fmt
            fmt_path.mkdir(exist_ok=True)
            format_paths[fmt] = fmt_path
            print(f"  {Fore.CYAN}✓{Style.RESET_ALL} {fmt_path.relative_to(base_path)}")
    
    return format_paths

def setup_workspace() -> tuple[Path, Path, dict, dict]:
    """
    Set up the workspace by getting a data path and creating in/out folder structures.
    """
    print(f"\n{Fore.WHITE}=== Workspace Setup ==={Style.RESET_ALL}\n")
    
    print("Enter the path for your DATA folder:")
    print(f"{Fore.CYAN}  Subfolders 'in/' and 'out/' will be created automatically{Style.RESET_ALL}")
    data_path = get_folder_path("Data folder path:")
    
    # Create in/out paths
    input_path = data_path / "in"
    output_path = data_path / "out"
    
    input_formats = create_folder_structure(input_path, INPUT_SUBFOLDERS, "input")
    output_formats = create_folder_structure(output_path, OUTPUT_SUBFOLDERS, "output")
    
    print(f"\n{Fore.GREEN}✓ Workspace setup complete!{Style.RESET_ALL}")
    print(f"  Input:  {Fore.CYAN}{input_path}{Style.RESET_ALL}")
    print(f"  Output: {Fore.CYAN}{output_path}{Style.RESET_ALL}")
    
    return input_path, output_path, input_formats, output_formats

def load_converter_module(module_path: Path) -> Optional[object]:
    """
    Load a converter module from file.
    """
    try:
        spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"{Fore.RED}Error loading {module_path.name}: {e}{Style.RESET_ALL}")
        return None

def discover_converters() -> list[ConverterInfo]:
    """
    Discover all available converters by scanning the converters directory.
    
    Returns:
        List of ConverterInfo objects for converters with valid CONVERTER_INFO metadata.
    """
    converters_dir = Path(__file__).parent / "converters"
    converters = []
    
    if not converters_dir.exists():
        return converters
    
    for f in converters_dir.glob("*.py"):
        if f.name.startswith("_"):
            continue
        
        module = load_converter_module(f)
        if module is None:
            continue
        
        # Check for CONVERTER_INFO metadata
        if not hasattr(module, "CONVERTER_INFO"):
            continue
        
        info = module.CONVERTER_INFO
        
        # Validate required fields
        required_fields = ["name", "input_format", "output_format", "input_category", "output_category"]
        if not all(field in info for field in required_fields):
            print(f"{Fore.YELLOW}Warning: {f.name} missing required CONVERTER_INFO fields{Style.RESET_ALL}")
            continue
        
        # Check for convert_file function (required for new-style converters)
        if not hasattr(module, "convert_file"):
            print(f"{Fore.YELLOW}Warning: {f.name} missing convert_file function{Style.RESET_ALL}")
            continue
        
        converters.append(ConverterInfo(
            name=info.get("name", f.stem),
            description=info.get("description", ""),
            input_format=info["input_format"].lower(),
            output_format=info["output_format"].lower(),
            input_category=info["input_category"].lower(),
            output_category=info["output_category"].lower(),
            module_path=f,
            module=module,
        ))
    return converters

def get_all_formats(converters:list[ConverterInfo]) -> tuple[set,set]:
    """
    Get all available input and output formats from converters."""
    input_formats = set()
    output_formats = set()
    
    for conv in converters:
        input_formats.add((conv.input_category, conv.input_format))
        output_formats.add((conv.output_category, conv.output_format))
    
    return input_formats, output_formats

def find_converter(converters:list[ConverterInfo], input_format:str, output_format:str) -> Optional[ConverterInfo]:
    """
    Find a converter that handles the specified input->output conversion.
    """
    input_format = input_format.lower()
    output_format = output_format.lower()
    
    for conv in converters:
        if conv.input_format == input_format and conv.output_format == output_format:
            return conv
    
    return None

def list_files_by_format(base_path:Path, category:str, format_ext:str) -> list[Path]:
    """
    List all files in the specified format folder.
    """
    folder = base_path / category / format_ext
    
    if not folder.exists():
        return []
    
    # Collect files with any case extension
    files = []
    for f in folder.iterdir():
        if f.is_file() and f.suffix.lower() in (f".{format_ext}", f".{format_ext.upper()}"):
            files.append(f)
    
    # Also check common alternate extensions
    alt_extensions = {
        "jpg": [".jpeg"],
        "heic": [".heif"],
    }
    
    if format_ext in alt_extensions:
        for alt in alt_extensions[format_ext]:
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() == alt:
                    files.append(f)
    
    return files

def convert_single_file(args:tuple) -> tuple[Path,bool,str]:
    """
    Convert a single file using the specified converter.
    Worker function for thread pool.
    
    Args:
        args: Tuple of (input_file, output_file, converter_module)
    
    Returns:
        Tuple of (input_file, success, message)
    """
    input_file, output_file, convert_fn = args
    try:
        success, message = convert_fn(input_file, output_file)
        return (input_file, success, message)
    except Exception as e:
        return (input_file, False, str(e))

def run_conversion_multithreaded(
    files:list[Path],
    output_dir:Path,
    output_ext:str,
    converter:ConverterInfo,
    num_workers:int=DEFAULT_WORKERS
) -> tuple[int, int]:
    """
    Run conversion on multiple files using a thread pool.
    
    Args:
        files: List of input file paths
        output_dir: Output directory path
        output_ext: Output file extension (without dot)
        converter: ConverterInfo object with loaded module
        num_workers: Number of worker threads
    
    Returns:
        Tuple of (success_count, fail_count)
    """
    print(f"\n{Fore.WHITE}=== {converter.name} ==={Style.RESET_ALL}")
    print(f"  Converting {Fore.GREEN}{len(files)}{Style.RESET_ALL} files using {Fore.CYAN}{num_workers}{Style.RESET_ALL} threads\n")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare conversion tasks
    tasks = []
    for input_file in files:
        output_file = output_dir / f"{input_file.stem}.{output_ext}"
        tasks.append((input_file, output_file, converter.module.convert_file))
    
    success_count = 0
    fail_count = 0
    
    # Run conversions with thread pool
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(convert_single_file, task): task[0] for task in tasks}
        
        # Use tqdm for progress bar
        with tqdm(total=len(files), desc="Converting", unit="file") as pbar:
            for future in as_completed(futures):
                input_file, success, message = future.result()
                
                if success:
                    tqdm.write(f"  {Fore.GREEN}✓{Style.RESET_ALL} {input_file.name} [{message}]")
                    success_count += 1
                else:
                    tqdm.write(f"  {Fore.RED}✗{Style.RESET_ALL} {input_file.name}: {message}")
                    fail_count += 1
                
                pbar.update(1)
    
    # Summary
    print(f"\n{Fore.WHITE}=== Conversion Complete ==={Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Successful: {success_count}{Style.RESET_ALL}")
    if fail_count > 0:
        print(f"  {Fore.RED}Failed: {fail_count}{Style.RESET_ALL}")
    print(f"  Output: {Fore.CYAN}{output_dir}{Style.RESET_ALL}")
    
    return success_count, fail_count

def select_from_list(items:list, prompt:str, display_fn=str) -> Optional[int]:
    """
    Display a numbered list and get user selection.
    """
    if not items:
        return None
    
    for i, item in enumerate(items, 1):
        print(f"  {Fore.CYAN}[{i}]{Style.RESET_ALL} {display_fn(item)}")
    print(f"  {Fore.CYAN}[0]{Style.RESET_ALL} Cancel")
    
    while True:
        try:
            choice = input(f"\n{Fore.GREEN}{prompt} (0-{len(items)}): {Style.RESET_ALL}").strip()
            
            if choice == "0" or choice.lower() in ("q", "quit", "exit", "cancel"):
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return idx
            else:
                print(f"{Fore.RED}Invalid choice{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a number{Style.RESET_ALL}")

def format_selection_flow(converters:list[ConverterInfo], input_path:Path, output_path:Path):
    """
    Interactive flow for selecting input format, output format, and running conversion.
    """
    print(f"\n{Fore.WHITE}=== Select Conversion ==={Style.RESET_ALL}\n")
    
    # Get unique input formats with file counts
    input_options = []
    for conv in converters:
        folder = input_path / conv.input_category / conv.input_format
        if folder.exists():
            files = list_files_by_format(input_path, conv.input_category, conv.input_format)
            if files:
                input_options.append({
                    "category": conv.input_category,
                    "format": conv.input_format,
                    "file_count": len(files),
                    "files": files,
                })
    
    # Remove duplicates
    seen = set()
    unique_inputs = []
    for opt in input_options:
        key = (opt["category"], opt["format"])
        if key not in seen:
            seen.add(key)
            unique_inputs.append(opt)
    
    if not unique_inputs:
        print(f"{Fore.YELLOW}No input files found in any supported format.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Place files in the appropriate input folders and try again.{Style.RESET_ALL}")
        return
    
    # Select input format
    print("Select INPUT format (source files):\n")
    
    def display_input(opt):
        return f"{opt['category']}/{opt['format']} ({opt['file_count']} files)"
    
    input_idx = select_from_list(unique_inputs, "Select input format", display_input)
    if input_idx is None:
        return
    
    selected_input = unique_inputs[input_idx]
    
    # Find converters that accept this input format
    matching_converters = [
        conv for conv in converters
        if conv.input_format == selected_input["format"]
        and conv.input_category == selected_input["category"]
    ]
    
    if not matching_converters:
        print(f"{Fore.RED}No converters available for this input format{Style.RESET_ALL}")
        return
    
    # Get unique output formats for this input
    output_options = []
    for conv in matching_converters:
        output_options.append({
            "category": conv.output_category,
            "format": conv.output_format,
            "converter": conv,
        })
    
    print(f"\nSelect OUTPUT format (for {selected_input['category']}/{selected_input['format']}):\n")
    
    def display_output(opt):
        return f"{opt['category']}/{opt['format']} - {opt['converter'].name}"
    
    output_idx = select_from_list(output_options, "Select output format", display_output)
    if output_idx is None:
        return
    
    selected_output = output_options[output_idx]
    converter = selected_output["converter"]
    
    # Get number of workers
    print(f"\nNumber of parallel threads (default: {DEFAULT_WORKERS}):")
    workers_input = input(f"{Fore.GREEN}Workers: {Style.RESET_ALL}").strip()
    
    try:
        num_workers = int(workers_input) if workers_input else DEFAULT_WORKERS
        num_workers = max(1, min(num_workers, 32))  # Clamp between 1 and 32
    except ValueError:
        num_workers = DEFAULT_WORKERS
    
    # Run conversion
    output_dir = output_path / selected_output["category"] / selected_output["format"]
    
    run_conversion_multithreaded(
        files=selected_input["files"],
        output_dir=output_dir,
        output_ext=selected_output["format"],
        converter=converter,
        num_workers=num_workers,
    )

if __name__ == "__main__":
    try:
        print_banner()
    
        # Discover available converters
        converters = discover_converters()
        
        if not converters:
            print(f"{Fore.RED}No converters found in converters/ directory{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Ensure converters have CONVERTER_INFO metadata and convert_file function{Style.RESET_ALL}")
            sys.exit(1)
        
        print(f"Found {Fore.GREEN}{len(converters)}{Style.RESET_ALL} converter(s):")
        for conv in converters:
            print(f"  • {conv.name}: {conv.input_format} → {conv.output_format}")
        
        # Setup workspace
        input_path, output_path, _, _ = setup_workspace()
        
        # Main loop
        while True:
            format_selection_flow(converters, input_path, output_path)
            
            cont = input(f"\n{Fore.GREEN}Run another conversion? (y/n): {Style.RESET_ALL}").strip().lower()
            if cont not in ("y", "yes"):
                print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}\n")
                break
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}\n")
        sys.exit(0)
