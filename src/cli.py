"""
Pricing Engine CLI Wrapper

This module provides a unified entry point for the pricing engine CLI tools.
For specific functionality, use the specialized CLI modules:

Zoho Analytics Data Management:
    python3 src/zoho_cli.py --help

Pricing Engine Operations:
    python3 src/pricing_cli.py --help

Examples:
    # Zoho Analytics operations (RECOMMENDED: use upsert commands)
    python3 src/zoho_cli.py upsert --report pnl_sms_by_month --year 2025 --month 5
    python3 src/zoho_cli.py upsert-range --report pnl_sms_by_month --start-year 2025 --start-month 1 --end-year 2025 --end-month 5

    # Legacy Zoho commands (WARNING: fetch-replace replaces entire table)
    python3 src/zoho_cli.py fetch-replace --report pnl_sms_by_month --year 2025 --month 5

    # Run pricing pipeline
    python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --verbose
"""

import argparse
import sys
import subprocess


def main():
    """Main CLI wrapper that directs to specialized modules."""
    parser = argparse.ArgumentParser(
        description="Pricing Engine CLI Wrapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Zoho Analytics operations (RECOMMENDED)
    python3 src/zoho_cli.py upsert --report pnl_sms_by_month --year 2025 --month 5
    python3 src/zoho_cli.py upsert-range --report pnl_sms_by_month --start-year 2025 --start-month 1 --end-year 2025 --end-month 5
    python3 src/zoho_cli.py load --report pnl_sms_by_month

    # Legacy Zoho commands (WARNING: fetch-replace replaces entire table)
    python3 src/zoho_cli.py fetch-replace --report pnl_sms_by_month --year 2025 --month 5

    # Pricing operations
    python3 src/pricing_cli.py run-pipeline
    python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --verbose
    python3 src/pricing_cli.py check-pricing --year 2024 --month 7
        """,
    )

    parser.add_argument(
        "module", choices=["zoho", "pricing"], help="Choose the CLI module to use"
    )

    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the selected module",
    )

    args = parser.parse_args()

    # Map module names to script paths
    module_map = {"zoho": "src/zoho_cli.py", "pricing": "src/pricing_cli.py"}

    script_path = module_map[args.module]

    # Execute the selected module with remaining arguments
    try:
        subprocess.run([sys.executable, script_path] + args.args, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"Error: Could not find {script_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
