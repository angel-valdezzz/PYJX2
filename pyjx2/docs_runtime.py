from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path


def package_root(base_file: str | None = None) -> Path:
    origin = Path(base_file) if base_file else Path(__file__)
    return origin.resolve().parent


def bundled_docs_index(base_file: str | None = None) -> Path | None:
    index = package_root(base_file) / "_bundled_docs" / "index.html"
    return index if index.is_file() else None


def repo_root(base_file: str | None = None) -> Path | None:
    root = package_root(base_file).parent
    if (root / "mkdocs.yml").is_file() and (root / "docs").is_dir():
        return root
    return None


def open_docs_target(target: str) -> None:
    if os.name == "nt":
        chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        edge = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
        if chrome.is_file():
            subprocess.Popen([str(chrome), "--new-window", "--start-fullscreen", target])
            return
        if edge.is_file():
            subprocess.Popen([str(edge), "--new-window", "--start-fullscreen", target])
            return

    webbrowser.open(target)
