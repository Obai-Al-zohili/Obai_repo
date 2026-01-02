# tester.py
import subprocess
import sys
import re
from typing import Tuple, Dict


# tester.py
import subprocess
import sys
import re
from typing import Tuple, Dict


def run_tests() -> Tuple[bool, str]:
    """Run pytest and return (all_passed, output)."""
    try:
        # Try pytest first
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--maxfail=1", "--disable-warnings", "-q"],
            capture_output=True,
            text=True,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, output
    except FileNotFoundError:
        # Fallback to simple tester if pytest is not available
        print("⚠️  pytest not found, using simple test runner")
        try:
            proc = subprocess.run(
                [sys.executable, "simple_tester.py"],
                capture_output=True,
                text=True,
            )
            output = (proc.stdout or "") + (proc.stderr or "")
            return proc.returncode == 0, output
        except Exception as e:
            return False, f"Error running tests: {str(e)}"


def run_pylint(target_files: list[str]) -> str:
    """Run pylint and return output."""
    proc = subprocess.run(
        [sys.executable, "-m", "pylint"] + target_files,
        capture_output=True,
        text=True,
    )
    return (proc.stdout or "") + (proc.stderr or "")


def parse_failure(output: str) -> Dict:
    """
    Try very hard to extract the failing file from pytest or pylint output.
    """

    # ---------- pytest patterns ----------
    pytest_patterns = [
        r"(?:FAILED|ERROR)\s+(\S+\.py)::(\S+)",
        r"(\S+\.py)::(\S+)\s+(?:FAILED|ERROR)",
        r'File "([^"]+\.py)", line \d+',
    ]

    for pat in pytest_patterns:
        m = re.search(pat, output)
        if m:
            file = m.group(1)
            test = m.group(2) if len(m.groups()) > 1 else None
            return {
                "file": file,
                "test": test,
                "trace": output[-3000:],
            }

    # ---------- pylint patterns ----------
    pylint_match = re.search(r"(\S+\.py):\d+:\d+:", output)
    if pylint_match:
        return {
            "file": pylint_match.group(1),
            "test": None,
            "trace": output[-3000:],
        }

    # ---------- Simple tester patterns ----------
    # Look for our custom test output that indicates buggy_code.py issues
    if "BUG:" in output and ("divide(" in output or "calculate_average(" in output or 
                            "get_first_element(" in output or "safe_int_conversion(" in output):
        return {
            "file": "buggy_code.py",  # Force it to fix the buggy code file
            "test": "simple_tests",
            "trace": output[-3000:],
        }

    # ---------- fallback ----------
    return {
        "file": None,
        "test": None,
        "trace": output[-3000:],
    }
