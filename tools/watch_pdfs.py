#!/usr/bin/env python3
"""Watch print-ready HTML/CSS files and regenerate the downloadable PDFs.

This is a small polling watcher with no extra dependency. It runs
``tools/generate_pdfs.py`` whenever the print sources change, which updates:

  * assets/pdf/Dongsik_Yoon_Resume.pdf
  * assets/pdf/Dongsik_Yoon_CV.pdf
  * assets/pdf/Dongsik_Yoon_Portfolio.pdf
  * ~/Downloads/Dongsik_Yoon_Resume.pdf
  * ~/Downloads/Dongsik_Yoon_CV.pdf
  * ~/Downloads/Dongsik_Yoon_Portfolio.pdf

Usage:
    python tools/watch_pdfs.py
    python tools/watch_pdfs.py --interval 2
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "tools" / "generate_pdfs.py"
WATCH_DIRS = (
    ROOT / "resume",
    ROOT / "cv",
    ROOT / "portfolio2026",
    ROOT / "assets" / "css",
)
WATCH_EXTS = {".html", ".css"}


def iter_sources() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in WATCH_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in WATCH_EXTS:
                files.append(path)
    return sorted(files)


def snapshot() -> dict[pathlib.Path, tuple[int, int]]:
    snap: dict[pathlib.Path, tuple[int, int]] = {}
    for path in iter_sources():
        try:
            stat = path.stat()
        except OSError:
            continue
        snap[path] = (stat.st_mtime_ns, stat.st_size)
    return snap


def run_generator() -> int:
    print("watch_pdfs: regenerating PDFs...", flush=True)
    result = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT)
    if result.returncode == 0:
        print("watch_pdfs: PDFs updated.", flush=True)
    else:
        print(f"watch_pdfs: generator failed with exit code {result.returncode}.", flush=True)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Polling interval in seconds. Default: 1.0")
    parser.add_argument("--no-initial", action="store_true",
                        help="Do not regenerate once at startup.")
    args = parser.parse_args(argv)

    before = snapshot()
    print("watch_pdfs: watching resume/, cv/, portfolio2026/, assets/css/")
    print("watch_pdfs: press Ctrl+C to stop.")
    if not args.no_initial:
        run_generator()
        before = snapshot()

    try:
        while True:
            time.sleep(max(args.interval, 0.2))
            after = snapshot()
            if after != before:
                before = after
                run_generator()
                before = snapshot()
    except KeyboardInterrupt:
        print("\nwatch_pdfs: stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
