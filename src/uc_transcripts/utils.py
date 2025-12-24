"""Shared utility functions."""

import shutil
from pathlib import Path
from typing import Optional


def zip_directory(dir_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Create a zip archive of a directory.

    Args:
        dir_path: Directory to zip
        output_path: Output path (default: {dir_path}.zip)

    Returns:
        Path to created zip file
    """
    if output_path is None:
        output_path = dir_path.parent / f"{dir_path.name}.zip"

    # Remove .zip extension if present (shutil.make_archive adds it)
    base_name = str(output_path.with_suffix(""))

    shutil.make_archive(base_name, "zip", dir_path)

    return Path(f"{base_name}.zip")


def unzip_file(zip_path: Path, extract_dir: Optional[Path] = None) -> None:
    """
    Extract zip file to directory.

    Args:
        zip_path: Path to zip file
        extract_dir: Directory to extract to (default: current directory)
    """
    if extract_dir is None:
        extract_dir = Path.cwd()

    shutil.unpack_archive(zip_path, extract_dir)
