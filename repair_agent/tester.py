# tester.py
import subprocess
import sys
import re
from typing import Tuple

def run_tests() -> Tuple[bool, str]:
    """Run pytest and return (all_passed, output)."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--maxfail=1", "--disable-warnings", "-q"],
        capture_output=True,
        text=True
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out

def run_pylint(target_files: list[str]) -> str:
    """Run pylint on a list of files and return output as a string."""
    args = [sys.executable, "-m", "pylint"] + target_files
    proc = subprocess.run(args, capture_output=True, text=True)
    return (proc.stdout or "") + (proc.stderr or "")

def parse_failure(output: str) -> dict:
    """Parse pytest failures or pylint errors and return info dict."""
    patterns = [
        r"(?:FAILED|ERROR)\s+(\S+\.py)::(\S+)",   
        r"(\S+\.py)::(\S+)\s+(?:FAILED|ERROR)",
        r"File \"([^\"]+\.py)\", line \d+",       
    ]
    for pat in patterns:
        m = re.search(pat, output)
        if m:
            file = m.group(1)
            test = m.group(2) if len(m.groups()) > 1 else None
            trace = output[-2000:]
            return {"file": file, "test": test, "trace": trace}

    # If pylint reports a missing import (F0401)
    f_match = re.search(r"(\S+\.py):\d+:\d+: F0401", output)
    if f_match:
        file = f_match.group(1)
        return {"file": file, "test": None, "trace": output[-2000:]}

    # fallback
    return {"file": None, "test": None, "trace": output[-2000:]}
