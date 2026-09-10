"""
Main orchestration pipeline for RBXLX Extractor.
"""

import argparse
import os
import sys
import time
from typing import List, Optional, Set

from .exporter.filesystem_exporter import FilesystemExporter
from .exporter.manifest_exporter import ManifestExporter
from .parser.rbxlx_parser import RbxlxParser
from .resolver.reference_resolver import ReferenceResolver
from .utils.logger import ExtractorLogger


def run_pipeline(
    input_file: str,
    output_dir: str = "output",
    verbose: bool = False,
    pretty: bool = False,
    include_properties: bool = True,
    extract_scripts: bool = True,
    strict: bool = False,
    services_filter: Optional[Set[str]] = None,
    rojo_style: bool = False,
) -> int:
    """
    Executes the end-to-end extraction pipeline.
    Returns exit code (0 for success).
    """
    logger = ExtractorLogger(verbose=verbose, strict=strict)
    start_total_time = time.time()

    logger.info("=" * 60)
    logger.info("Roblox RBXLX Extractor (Standalone)")
    logger.info(f"Input : {input_file}")
    logger.info(f"Output: {output_dir}")
    logger.info("=" * 60)

    try:
        # Step 1: Parse RBXLX file
        logger.info("Step 1/5: Parsing RBXLX XML stream...")
        parser = RbxlxParser(logger=logger)
        data_model, instances_by_referent = parser.parse_file(
            input_file, filter_services=services_filter
        )

        # Step 2: Resolve References
        logger.info("Step 2/5: Resolving Object references...")
        resolver = ReferenceResolver(logger=logger, instances_by_referent=instances_by_referent)
        resolver.resolve_all(data_model)

        # Step 3: Export Filesystem Tree
        logger.info("Step 3/5: Exporting Filesystem Tree & Scripts...")
        fs_exporter = FilesystemExporter(
            logger=logger,
            output_dir=output_dir,
            extract_scripts=extract_scripts,
            include_properties=include_properties,
            pretty=pretty,
            rojo_style=rojo_style,
        )
        exported_scripts = fs_exporter.export_tree(data_model)

        # Step 4: Write Manifest
        logger.info("Step 4/5: Writing manifest.json...")
        manifest_exporter = ManifestExporter(logger=logger, pretty=pretty)
        services_names = [s.name for s in data_model.children]
        manifest_path = manifest_exporter.export_manifest(
            source_file=input_file,
            output_dir=output_dir,
            services=services_names,
            scripts=exported_scripts,
            instances_summary=fs_exporter.exported_instances_summary if verbose else None,
        )
        logger.info(f"Manifest saved to: {manifest_path}")

        # Step 5: Write Warnings Log
        logger.info("Step 5/5: Writing warnings.log...")
        warnings_path = logger.write_warnings_log(output_dir)
        logger.info(f"Warnings saved to: {warnings_path} ({len(logger.warnings)} warnings)")

        total_elapsed = time.time() - start_total_time
        logger.info("=" * 60)
        logger.info(f"Done in {total_elapsed:.2f}s!")
        logger.info(f"- Instances : {logger.stats['totalInstances']}")
        logger.info(f"- Scripts   : {logger.stats['totalScripts']} "
                    f"({logger.stats['serverScripts']} server, "
                    f"{logger.stats['localScripts']} client, "
                    f"{logger.stats['moduleScripts']} module)")
        logger.info(f"- Properties: {logger.stats['totalProperties']}")
        logger.info(f"- References: {logger.stats['totalReferences']}")
        logger.info(f"- Warnings  : {logger.stats['totalWarnings']}")
        logger.info("=" * 60)
        return 0

    except Exception as ex:
        logger.error(category="FatalError", message=f"Pipeline failed: {ex}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standalone Roblox RBXLX parser and filesystem extractor (No Roblox Studio required)."
    )
    parser.add_argument("input", help="Path to Roblox .rbxlx XML place file")
    parser.add_argument(
        "-o", "--output", default="output", help="Directory where files will be exported (default: output/)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    parser.add_argument(
        "-p", "--pretty", action="store_true", help="Format JSON files with indent=2 (default: compact for speed)"
    )
    parser.add_argument(
        "--no-properties",
        dest="include_properties",
        action="store_false",
        default=True,
        help="Exclude properties block from instance.json metadata",
    )
    parser.add_argument(
        "--no-scripts",
        dest="extract_scripts",
        action="store_false",
        default=True,
        help="Do not extract script source files",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat any warning or broken reference as a fatal error"
    )
    parser.add_argument(
        "--services",
        help="Comma-separated list of top-level services to extract (e.g. ServerScriptService,Workspace)",
    )
    parser.add_argument(
        "--rojo-style",
        action="store_true",
        help="Use init.server.lua / init.client.lua / init.lua for scripts that have child instances",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    services_set = set(s.strip() for s in args.services.split(",")) if args.services else None

    return run_pipeline(
        input_file=args.input,
        output_dir=args.output,
        verbose=args.verbose,
        pretty=args.pretty,
        include_properties=args.include_properties,
        extract_scripts=args.extract_scripts,
        strict=args.strict,
        services_filter=services_set,
        rojo_style=args.rojo_style,
    )


if __name__ == "__main__":
    sys.exit(main())
