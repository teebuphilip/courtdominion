#!/usr/bin/env python3
"""
Bridge DBB2 engine output to the CourtDominion app data directory.

Copies the 4 CD JSON files from dbb2-engine/output/ into the CD app's
data directory. Optionally validates before copying.

Usage:
    python bridge_to_cd.py                                    # Auto-detect CD app
    python bridge_to_cd.py --cd-data-dir /path/to/data        # Explicit target
    python bridge_to_cd.py --validate                         # Validate first
    python bridge_to_cd.py --source-dir /tmp/output           # Custom source
"""

import argparse
import shutil
import sys
from pathlib import Path

CD_FILES = ["players.json", "projections.json", "risk.json", "insights.json"]

# Auto-detect: sibling courtdominion-app repo
DEFAULT_CD_DATA = (
    Path(__file__).resolve().parent.parent
    / "courtdominion-app"
    / "data"
    / "outputs"
)


def bridge(source_dir: str, cd_data_dir: str = None, validate: bool = False) -> bool:
    """
    Copy 4 CD JSON files from source to CD app data directory.

    Returns True on success.
    """
    src = Path(source_dir)
    dst = Path(cd_data_dir) if cd_data_dir else DEFAULT_CD_DATA

    # Verify source files exist
    missing = [f for f in CD_FILES if not (src / f).exists()]
    if missing:
        print(f"ERROR: Missing source files: {missing}")
        print(f"  Run 'python run_engine.py' first to generate output.")
        return False

    # Optional validation
    if validate:
        print("Validating output before bridge...")
        from engine.validate import validate_output_dir, validate_cross_file_consistency

        valid, errors = validate_output_dir(str(src))
        if not valid:
            print(f"  Schema validation FAILED ({len(errors)} errors):")
            for e in errors[:5]:
                print(f"    - {e}")
            return False
        print("  Schema validation: PASS")

        valid2, errors2 = validate_cross_file_consistency(str(src))
        if not valid2:
            print(f"  Cross-file consistency FAILED ({len(errors2)} errors):")
            for e in errors2[:5]:
                print(f"    - {e}")
            return False
        print("  Cross-file consistency: PASS")

    # Create target directory
    dst.mkdir(parents=True, exist_ok=True)

    # Copy files
    print(f"\nBridging: {src} -> {dst}")
    for filename in CD_FILES:
        src_file = src / filename
        dst_file = dst / filename
        shutil.copy2(src_file, dst_file)
        print(f"  Copied: {filename}")

    print(f"\nDone. {len(CD_FILES)} files bridged to CD app.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Bridge DBB2 output to CourtDominion app",
    )
    parser.add_argument(
        "--source-dir",
        default="output",
        help="DBB2 engine output directory (default: output/)",
    )
    parser.add_argument(
        "--cd-data-dir",
        default=None,
        help=f"CD app data directory (default: {DEFAULT_CD_DATA})",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output before copying",
    )
    args = parser.parse_args()

    success = bridge(args.source_dir, args.cd_data_dir, args.validate)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
