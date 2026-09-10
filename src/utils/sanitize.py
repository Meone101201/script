"""
Path and filename sanitization utilities.
Handles OS-reserved characters, Windows device names, trailing characters, and sibling collisions.
"""

import os
import re
from typing import Dict, Set

# Windows forbidden characters: < > : " / \ | ? * and ASCII 0-31
INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Windows reserved device names (case-insensitive)
RESERVED_NAMES: Set[str] = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_filesystem_name(name: str, replacement: str = "_") -> str:
    r"""
    Sanitizes a Roblox instance name into a safe filesystem name for folders and files.
    - Replaces invalid characters (<, >, :, ", /, \, |, ?, *, control chars)
    - Strips or pads trailing dots and spaces (illegal on Windows)
    - Escapes reserved Windows names (e.g. CON, NUL)
    - Handles empty names
    """
    if not name or not isinstance(name, str):
        return "Unnamed"

    # Replace invalid chars
    clean = INVALID_CHARS_RE.sub(replacement, name)

    # Strip leading/trailing spaces and dots
    clean = clean.strip(". ")

    if not clean:
        clean = "Unnamed"

    # Check if base name without extension is a reserved Windows device name
    stem = clean.split(".")[0].upper()
    if stem in RESERVED_NAMES:
        clean = f"_{clean}"

    return clean


class SiblingCollisionResolver:
    """
    Tracks names allocated within a single directory level to prevent overwriting
    when multiple Roblox instances share the same name under the same parent.
    Case-insensitive on Windows to prevent case-clashes.
    """

    def __init__(self, case_insensitive: bool = True):
        self.case_insensitive = case_insensitive
        self._allocated_names: Set[str] = set()
        self._stem_counts: Dict[str, int] = {}

    def get_unique_name(self, raw_name: str, extension: str = "") -> str:
        """
        Returns a unique sanitized filename or folder name.
        If extension is provided (e.g. '.server.lua'), the extension is preserved.
        """
        sanitized = sanitize_filesystem_name(raw_name)
        base = sanitized
        ext = extension

        if not ext and "." in sanitized:
            # If extension wasn't explicitly passed, don't split unless needed
            pass

        key_candidate = f"{base}{ext}"
        lookup_key = key_candidate.lower() if self.case_insensitive else key_candidate

        if lookup_key not in self._allocated_names:
            self._allocated_names.add(lookup_key)
            base_key = base.lower() if self.case_insensitive else base
            self._stem_counts[base_key] = 1
            return key_candidate

        # Collision found! Find next number
        base_key = base.lower() if self.case_insensitive else base
        count = self._stem_counts.get(base_key, 1) + 1

        while True:
            candidate = f"{base}_{count}{ext}"
            lookup_key = candidate.lower() if self.case_insensitive else candidate
            if lookup_key not in self._allocated_names:
                self._allocated_names.add(lookup_key)
                self._stem_counts[base_key] = count
                return candidate
            count += 1


def ensure_extended_path(path: str) -> str:
    """
    Prepends extended path prefix (\\\\?\\) on Windows if path is absolute and long,
    avoiding the MAX_PATH (260 char) limit.
    """
    if os.name != "nt":
        return path

    abs_path = os.path.abspath(path)
    if abs_path.startswith("\\\\?\\") or abs_path.startswith("//?/"):
        return abs_path

    if abs_path.startswith("\\\\"):
        # UNC path
        return "\\\\?\\UNC\\" + abs_path[2:]

    return "\\\\?\\" + abs_path
