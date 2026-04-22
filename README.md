<a name="readme-top"></a>

<br />
<div align="center">
  <a href="https://github.com/arsonite/clover">
    <img src="./files/media/icon/clover-logo-color.svg" alt="clover icon" width="80" height="80">
  </a>

<h3 align="center"><b>clover</b></h3>

  <p align="center">

A fast video, image and audio converter.
Includes a CLI.
<br />
<a href="https://github.com/arsonite/clover/issues">Report Bug</a>
·
<a href="https://github.com/arsonite/clover/issues">Request Feature</a>

  </p>
</div>

## Setup

1. Run the setup script to create the virtual environment and install dependencies:

```bash
chmod +x scripts/setup
./scripts/setup
```

2. Ensure you have **ffmpeg** installed on your system:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

## Usage

1. Activate the virtual environment:

```bash
source clover-venv/bin/activate
```

2. Run the main script:

```bash
python main.py
```

3. Follow the prompts to:
    - Set your input folder (where source files go)
    - Set your output folder (where converted files are saved)
    - Select input format (shows only formats with files present)
    - Select output format (shows available converters)
    - Set number of worker threads for parallel conversion

## Folder Structure

After setup, your input and output folders will have this structure:

```
input_folder/
├── video/
│   ├── mov/    ← Place .mov files here
│   ├── mp4/
│   ├── avi/
│   └── ...
├── image/
│   ├── jpg/
│   ├── png/
│   └── ...
└── audio/
    ├── mp3/
    ├── wav/
    └── ...

output_folder/
├── video/
│   ├── mp4/
│   ├── webm/
│   └── ...
├── image/
│   ├── jpg/    ← Converted JPEGs appear here
│   ├── png/
│   └── ...
└── audio/
    ├── mp3/
    ├── wav/
    └── ...
```

## Available Converters

### MOV First Frame to JPEG

Extracts the first frame from `.mov` video files and saves as JPEG.

- **Input:** `input_folder/video/mov/*.mov`
- **Output:** `output_folder/image/jpg/*.jpg`

### HEIC to JPEG

Converts HEIC/HEIF images (iPhone photos) to JPEG format.

- **Input:** `input_folder/image/heic/*.heic`
- **Output:** `output_folder/image/jpg/*.jpg`

## Adding New Converters

Create a new Python file in `converters/` with `CONVERTER_INFO` metadata and a `convert_file` function:

```python
# converters/my_converter.py
from pathlib import Path

# Required metadata for automatic discovery
CONVERTER_INFO = {
    "name": "My Converter",
    "description": "Description of what this converter does",
    "input_format": "ext",       # e.g., "heic", "mov", "mp3"
    "output_format": "ext",      # e.g., "jpg", "mp4", "wav"
    "input_category": "image",   # "video", "image", or "audio"
    "output_category": "image",  # "video", "image", or "audio"
}

def convert_file(input_path: Path, output_path: Path) -> tuple[bool, str]:
    """
    Convert a single file. Called by main.py for multithreaded conversion.

    Args:
        input_path: Path to input file
        output_path: Path for output file

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Your conversion logic here
        return True, "1920x1080"  # Return info about the conversion
    except Exception as e:
        return False, str(e)
```

The converter will automatically appear in the format selection menu when files of the input format are present.

## Multithreaded Conversion

clover uses multithreaded conversion by default. When running a conversion, you can specify the number of worker threads (default: 4). This significantly speeds up batch conversions.

## Dependencies

Core libraries included:

- **opencv-python** - Video/image processing
- **moviepy** - Video editing
- **ffmpeg-python** - FFmpeg bindings
- **Pillow** - Image manipulation
- **pillow-heif** - HEIC/HEIF support
- **pydub** - Audio processing
- **librosa** - Audio analysis

See `requirements.txt` for the full list.
