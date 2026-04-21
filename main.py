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
from colorama import Fore, Style
from colorama import init as init_colorama
from tqdm import tqdm

# Initialize colorama for cross-platform colored output
init_colorama()

# Default number of worker threads
DEFAULT_WORKERS = 4

@dataclass
class ConverterInfo:
    """Information about a discovered converter."""
    name: str
    description: str
    input_format: str
    output_format: str
    input_category: str
    output_category: str
    module_path: Path
    instance: object  # The converter instance

def print_banner():
    """
    Print the application banner.
    """
    banner = f"""
{Fore.CYAN}╔════════════════════════════════════╗
║            {Fore.WHITE}C L O V E R{Fore.CYAN}             ║
║   {Fore.YELLOW}Video • Image • Audio Converter{Fore.CYAN}  ║
╚════════════════════════════════════╝{Style.RESET_ALL}
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

def build_folder_maps(converters: list[ConverterInfo]) -> tuple[dict, dict]:
    """
    Build input and output folder structure maps from discovered converters.
    
    Args:
        converters: List of discovered ConverterInfo objects
        
    Returns:
        Tuple of (input_subfolders, output_subfolders) dicts mapping category -> [formats]
    """
    input_subfolders = {}
    output_subfolders = {}
    
    for conv in converters:
        # Build input folder map
        if conv.input_category not in input_subfolders:
            input_subfolders[conv.input_category] = []
        if conv.input_format not in input_subfolders[conv.input_category]:
            input_subfolders[conv.input_category].append(conv.input_format)
        
        # Build output folder map
        if conv.output_category not in output_subfolders:
            output_subfolders[conv.output_category] = []
        if conv.output_format not in output_subfolders[conv.output_category]:
            output_subfolders[conv.output_category].append(conv.output_format)
    
    return input_subfolders, output_subfolders


def setup_workspace(converters: list[ConverterInfo]) -> tuple[Path, Path, dict, dict]:
    """
    Set up the workspace by getting a data path and creating in/out folder structures.
    Folder structure is built dynamically based on discovered converters.
    
    Args:
        converters: List of discovered ConverterInfo objects
    """
    print(Fore.WHITE)
    print('#######################')
    print(f'### Workspace Setup ###')
    print('#######################')
    print(Style.RESET_ALL)
    
    print('Enter the path for your DATA folder:')
    print(f'{Fore.CYAN}  Subfolders "in" and "out" will be created automatically{Style.RESET_ALL}')
    data_path = get_folder_path('Data folder path:')
    
    # Build folder structure maps from discovered converters
    input_subfolders, output_subfolders = build_folder_maps(converters)
    
    # Create in/out paths
    input_path = data_path / 'in'
    output_path = data_path / 'out'
    
    input_formats = create_folder_structure(input_path, input_subfolders, 'input')
    output_formats = create_folder_structure(output_path, output_subfolders, 'output')
    
    print(f'\n{Fore.GREEN}✓ Workspace setup complete!{Style.RESET_ALL}')
    print(f'  Input:  {Fore.CYAN}{input_path}{Style.RESET_ALL}')
    print(f'  Output: {Fore.CYAN}{output_path}{Style.RESET_ALL}')
    
    return input_path, output_path, input_formats, output_formats

def load_converter_module(module_path: Path) -> Optional[object]:
    """
    Load a converter module from file.
    """
    try:
        # Build the module name with package context for relative imports
        module_name = f'converters.{module_path.stem}'
        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path,
            submodule_search_locations=[str(module_path.parent)]
        )
        module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules so relative imports work
        sys.modules[module_name] = module
        
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f'{Fore.RED}Error loading {module_path.name}: {e}{Style.RESET_ALL}')
        return None

def discover_converters() -> list[ConverterInfo]:
    """
    Discover all available converters by scanning the converters directory.
    
    Looks for classes that inherit from BaseConverter and have the required
    class attributes defined.
    
    Returns:
        List of ConverterInfo objects for valid converter classes.
    """
    import inspect
    
    converters_dir = Path(__file__).parent / "converters"
    converters = []
    
    if not converters_dir.exists():
        return converters
    
    for f in converters_dir.glob("*.py"):
        if f.name.startswith("_") or f.name == "base_converter.py":
            continue
        
        module = load_converter_module(f)
        if module is None:
            continue
        
        # Find all classes in the module that inherit from BaseConverter
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Skip classes not defined in this module
            if obj.__module__ != module.__name__:
                continue
            
            # Check if it inherits from a class named BaseConverter
            # (using name check to avoid issues with different module contexts)
            base_names = [base.__name__ for base in obj.__mro__]
            if "BaseConverter" not in base_names:
                continue
            
            # Validate required class attributes
            required_attrs = ["name", "input_format", "output_format", "input_category", "output_category"]
            missing = [attr for attr in required_attrs if not hasattr(obj, attr) or getattr(obj, attr) is None]
            
            if missing:
                print(f"{Fore.YELLOW}Warning: {f.name}:{name} missing required attributes: {missing}{Style.RESET_ALL}")
                continue
            
            # Instantiate the converter
            try:
                instance = obj()
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: {f.name}:{name} failed to instantiate: {e}{Style.RESET_ALL}")
                continue
            
            converters.append(ConverterInfo(
                name=obj.name,
                description=getattr(obj, "description", ""),
                input_format=obj.input_format.lower(),
                output_format=obj.output_format.lower(),
                input_category=obj.input_category.lower(),
                output_category=obj.output_category.lower(),
                module_path=f,
                instance=instance,
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
    alternative_extensions = {
        'jpg': ['.jpeg'],
        'heic': ['.heif'],
    }
    if format_ext in alternative_extensions:
        for alt in alternative_extensions[format_ext]:
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

def run_conversion_multithreaded(files:list[Path],
                                 output_dir:Path,
                                 output_ext:str,
                                 converter:ConverterInfo,
                                 num_workers:int=DEFAULT_WORKERS) -> tuple[int, int]:
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
        tasks.append((input_file, output_file, converter.instance.convert_file))
    
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
            print(f'{Fore.RED}No converters found in converters/ directory{Style.RESET_ALL}')
            print(f'{Fore.CYAN}Ensure converters have CONVERTER_INFO metadata and convert_file function{Style.RESET_ALL}')
            sys.exit(1)
        
        print(f'Found {Fore.GREEN}{len(converters)}{Style.RESET_ALL} converter(s)')
        
        # Setup workspace (folder structure is built from discovered converters)
        input_path, output_path, _, _ = setup_workspace(converters)
        
        # Main loop
        while True:
            format_selection_flow(converters, input_path, output_path)
            
            cont = input(f'\n{Fore.GREEN}Run another conversion? (y/n): {Style.RESET_ALL}').strip().lower()
            if cont not in ('y', 'yes'):
                print(f'\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}\n')
                break
    except KeyboardInterrupt:
        print(f'\n\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}\n')
        sys.exit(0)
