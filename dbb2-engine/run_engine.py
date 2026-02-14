#!/usr/bin/env python3
"""
CLI entry point for the DBB2 projection engine.

Usage:
    python run_engine.py                     # Default: project + export to ./output/
    python run_engine.py --output-dir /tmp   # Custom output directory
    python run_engine.py --validate          # Validate output against CD schemas
    python run_engine.py --seasons 5         # Override season count (default: 3)
"""

import argparse
import sys

from engine import project_all_season, export_json, export_betting


def main():
    parser = argparse.ArgumentParser(
        description="DBB2 Basketball Projection Engine",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for output JSON files (default: output/)",
    )
    parser.add_argument(
        "--seasons",
        type=int,
        default=3,
        help="Number of recent seasons to load (default: 3)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run schema validation after export",
    )
    parser.add_argument(
        "--no-betting",
        action="store_true",
        help="Skip betting_contract.json export",
    )
    args = parser.parse_args()

    # 1. Project
    print(f"=== DBB2 Engine — {args.seasons} season(s) ===\n")
    contexts, projections, auction_values = project_all_season(args.seasons)

    # 2. Export CD JSON
    print()
    files = export_json(contexts, projections, auction_values, args.output_dir)

    # 3. Export betting contract
    if not args.no_betting:
        export_betting(contexts, projections, args.output_dir)

    # 4. Summary
    print(f"\n=== Summary ===")
    print(f"  Players projected: {len(projections)}")
    print(f"  Output directory:  {args.output_dir}/")
    print(f"  Files written:     {len(files)} CD JSON" + (" + betting_contract.json" if not args.no_betting else ""))

    # 5. Validate
    if args.validate:
        print(f"\n=== Validation ===")
        from engine.validate import validate_output_dir, validate_cross_file_consistency

        valid, errors = validate_output_dir(args.output_dir)
        if valid:
            print("  Schema validation: PASS")
        else:
            print(f"  Schema validation: FAIL ({len(errors)} errors)")
            for e in errors:
                print(f"    - {e}")

        valid2, errors2 = validate_cross_file_consistency(args.output_dir)
        if valid2:
            print("  Cross-file consistency: PASS")
        else:
            print(f"  Cross-file consistency: FAIL ({len(errors2)} errors)")
            for e in errors2:
                print(f"    - {e}")

        if not valid or not valid2:
            sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
