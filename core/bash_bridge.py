"""Secure Automation Bridge for Executing Shell Scripts from Python.

Encapsulates subprocess invocation with strict whitelisting, arguments sanitization,
timeout enforcement, and graceful cross-platform shell detection.
"""

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from core.logger import log_event

# Whitelisted script basenames permitted for execution
ALLOWED_SCRIPTS = {
    "sysinfo.sh",
    "collect_logs.sh",
    "run_tests.sh",
    "serve.sh",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_bash_executable() -> Optional[str]:
    """Locate a valid Bash executable across Linux, WSL, and Windows environments."""
    # 1. Standard PATH lookup (Linux / WSL / Git Bash in PATH)
    bash_path = shutil.which("bash")
    if bash_path:
        return bash_path

    # 2. Windows specific Git Bash locations
    windows_candidates = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ]
    for candidate in windows_candidates:
        if os.path.exists(candidate):
            return candidate

    return None


def run_script(
    script_name: str,
    args: Optional[List[str]] = None,
    timeout_sec: int = 45,
) -> Dict[str, Any]:
    """Execute a whitelisted shell script in a secure subprocess.

    Args:
        script_name: Basename of script in project root (must be in ALLOWED_SCRIPTS)
        args: Optional list of command line arguments
        timeout_sec: Maximum execution duration before raising timeout

    Returns:
        Dict containing {success: bool, return_code: int, stdout: str, stderr: str}
    """
    if script_name not in ALLOWED_SCRIPTS:
        msg = f"Security Violation: Script '{script_name}' is not in the allowed execution whitelist."
        log_event("bash_bridge", msg, level="ERROR")
        return {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": msg,
        }

    script_path = PROJECT_ROOT / script_name
    if not script_path.exists():
        msg = f"Target script '{script_name}' does not exist at {script_path}."
        log_event("bash_bridge", msg, level="ERROR")
        return {
            "success": False,
            "return_code": -2,
            "stdout": "",
            "stderr": msg,
        }

    cmd_args = args or []
    bash_bin = find_bash_executable()

    if not bash_bin:
        msg = "Bash interpreter not detected on this system."
        log_event("bash_bridge", msg, level="WARNING")
        return {
            "success": False,
            "return_code": -3,
            "stdout": "",
            "stderr": msg,
        }

    # Construct execution command using list form (shell=False)
    # Convert script path to forward slashes for bash compatibility
    full_cmd = [bash_bin, str(script_path.as_posix())] + cmd_args

    log_event("bash_bridge", f"Executing shell script: {script_name} with args: {cmd_args}")

    try:
        proc = subprocess.run(
            full_cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            shell=False,
        )

        success = (proc.returncode == 0)
        log_event(
            "bash_bridge",
            f"Script '{script_name}' finished with exit code {proc.returncode}",
            level="INFO" if success else "WARNING"
        )

        return {
            "success": success,
            "return_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    except subprocess.TimeoutExpired as exc:
        msg = f"Execution timed out after {timeout_sec} seconds."
        log_event("bash_bridge", f"Script '{script_name}' timed out: {msg}", level="ERROR")
        return {
            "success": False,
            "return_code": -4,
            "stdout": exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            "stderr": msg,
        }
    except Exception as exc:
        msg = f"Unexpected execution error: {str(exc)}"
        log_event("bash_bridge", f"Exception running '{script_name}': {msg}", level="ERROR", exc_info=exc)
        return {
            "success": False,
            "return_code": -5,
            "stdout": "",
            "stderr": msg,
        }
