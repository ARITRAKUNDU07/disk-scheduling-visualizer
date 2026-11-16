"""OS Resource Manager Simulator (osrm) - Primary Application Entry Point.

Course: Operating Systems Laboratory (ENSC-351), B.Tech Semester V
Target: Ubuntu 24.04 LTS (WSL2 / Linux Kernel), Python 3.10+

Usage:
    python3 main.py          # Interactive prompt to choose Web or CLI
    python3 main.py --web    # Launch Web Dashboard on loopback interface
    python3 main.py --cli    # Launch Interactive Terminal Menu
    python3 main.py --port N # Set custom port for web server (default: 8080)
"""

import argparse
from pathlib import Path
import sys

from core.logger import init_logging, log_event

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="osrm",
        description="OS Resource Manager Simulator (osrm) - Flagship Capstone Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--web", action="store_true", help="Launch the local Web Dashboard (default: 127.0.0.1:8080)")
    group.add_argument("--cli", action="store_true", help="Launch the Interactive Terminal ANSI Menu")
    group.add_argument("--test", action="store_true", help="Execute the complete test suite and exit")

    parser.add_argument("--port", type=int, default=8080, help="Port for web server (default: 8080)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0 (ENSC-351 Capstone)")

    return parser.parse_args()


def interactive_mode_select() -> str:
    print("\n" + "=" * 66)
    print("       OS RESOURCE MANAGER SIMULATOR (OSRM) - LAUNCHER")
    print(" Operating Systems Laboratory (ENSC-351), B.Tech Semester V")
    print("=" * 66)
    print("  [1] Launch Themed Local Web Dashboard (Recommended)")
    print("  [2] Launch Interactive Terminal Menu (CLI Mode)")
    print("  [3] Run Automated Test Suite")
    print("  [0] Exit")
    print("=" * 66)
    try:
        choice = input("Select interface mode [1-3, default=1]: ").strip()
        if choice in ("2", "cli", "c"):
            return "cli"
        elif choice in ("3", "test", "t"):
            return "test"
        elif choice in ("0", "exit", "quit", "q"):
            return "exit"
        else:
            return "web"
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        return "exit"


def main() -> None:
    # Ensure logs directory and logging system initialized
    log_file = init_logging(PROJECT_ROOT / "logs")
    log_event("main", f"OSRM started with arguments: {sys.argv}")

    args = parse_arguments()

    selected_mode = None
    if args.web:
        selected_mode = "web"
    elif args.cli:
        selected_mode = "cli"
    elif args.test:
        selected_mode = "test"
    else:
        # No explicit mode flag passed; prompt user
        selected_mode = interactive_mode_select()

    if selected_mode == "exit":
        sys.exit(0)

    if selected_mode == "test":
        from core.bash_bridge import run_script
        res = run_script("run_tests.sh")
        print(res["stdout"])
        sys.exit(res["return_code"])

    elif selected_mode == "cli":
        from ui.menus import run_cli_menu
        run_cli_menu()

    elif selected_mode == "web":
        from web.server import run_web_server
        run_web_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
