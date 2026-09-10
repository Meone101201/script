"""
Logger and Warning Collector for RBXLX Extractor.
Collects warnings, tracks statistics, formats console output, and writes warnings.log.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import os


@dataclass
class ExtractionWarning:
    level: str
    category: str
    message: str
    target: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def format_log_line(self) -> str:
        loc = f" [{self.target}]" if self.target else ""
        return f"[{self.level.upper()}][{self.category}]{loc} {self.message}"


class ExtractorLogger:
    def __init__(self, verbose: bool = False, strict: bool = False):
        self.verbose = verbose
        self.strict = strict
        self.warnings: List[ExtractionWarning] = []
        self.category_counts: Dict[str, int] = {}
        self.stats: Dict[str, int] = {
            "totalInstances": 0,
            "totalScripts": 0,
            "serverScripts": 0,
            "localScripts": 0,
            "moduleScripts": 0,
            "totalProperties": 0,
            "totalReferences": 0,
            "totalWarnings": 0,
        }

    def info(self, msg: str, prefix: str = "") -> None:
        p = f"[{prefix}] " if prefix else ""
        print(f"{p}{msg}")

    def debug(self, msg: str) -> None:
        if self.verbose:
            print(f"  [DEBUG] {msg}")

    def warn(self, category: str, message: str, target: Optional[str] = None) -> None:
        warning = ExtractionWarning(
            level="WARNING",
            category=category,
            message=message,
            target=target,
        )
        self.warnings.append(warning)
        self.category_counts[category] = self.category_counts.get(category, 0) + 1
        self.stats["totalWarnings"] += 1

        if self.verbose:
            print(f"  {warning.format_log_line()}")

        if self.strict:
            raise RuntimeError(f"Strict mode failure: {warning.format_log_line()}")

    def error(self, category: str, message: str, target: Optional[str] = None) -> None:
        warning = ExtractionWarning(
            level="ERROR",
            category=category,
            message=message,
            target=target,
        )
        self.warnings.append(warning)
        self.category_counts[category] = self.category_counts.get(category, 0) + 1
        self.stats["totalWarnings"] += 1

        print(f"  {warning.format_log_line()}")

        if self.strict:
            raise RuntimeError(f"Strict mode failure: {warning.format_log_line()}")

    def write_warnings_log(self, output_dir: str) -> str:
        """Writes warnings.log to output directory. Returns file path."""
        os.makedirs(output_dir, exist_ok=True)
        log_path = os.path.join(output_dir, "warnings.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# RBXLX Extractor Warnings Log\n")
            f.write(f"# Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"# Total warnings/errors: {len(self.warnings)}\n\n")

            if self.category_counts:
                f.write("## Summary by Category\n")
                for cat, count in sorted(self.category_counts.items()):
                    f.write(f"- {cat}: {count}\n")
                f.write("\n## Details\n")

            for w in self.warnings:
                f.write(w.format_log_line() + "\n")

        return log_path
