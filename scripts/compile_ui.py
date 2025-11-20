#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def compile_ui_files() -> int:
    """Find and compile all .ui files to .py files using pyside6-uic."""
    project_root = Path(__file__).parent.parent
    msms_dir = project_root / "msms"

    ui_files = list(msms_dir.rglob("*.ui"))

    if not ui_files:
        print("No .ui files found.")
        return 0

    failed = False
    for ui_file in ui_files:
        # Determine output file name: main_window.ui -> ui_main_window.py
        output_file = ui_file.parent / f"ui_{ui_file.stem}.py"

        print(f"Compiling {ui_file} -> {output_file}...")

        try:
            subprocess.run(
                ["pyside6-uic", str(ui_file), "-o", str(output_file)], check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error compiling {ui_file}:")
            print(e.stderr)
            failed = True
        except FileNotFoundError:
            print("Error: pyside6-uic not found. Is PySide6 installed?")
            return 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(compile_ui_files())
