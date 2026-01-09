# tester.py
import subprocess
import sys
import re
import os
from typing import Tuple

def run_tests() -> Tuple[bool, str]:
    """Run pytest on all test files and return (all_passed, output)."""
    # Look for tests directory in current directory or parent directory
    test_dirs = ["tests/", "../tests/", "test/", "../test/"]
    test_dir = None
    
    for td in test_dirs:
        if os.path.exists(td):
            test_dir = td
            break
    
    if not test_dir:
        # If no test directory found, try running pytest on current directory
        test_dir = "."
    
    print(f"🧪 Running tests in: {test_dir}")
    
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", test_dir, "--maxfail=1", "--disable-warnings", "-q"],
        capture_output=True,
        text=True,
        cwd="."
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
    print(f"🔍 Parsing failure from output (length: {len(output)})")
    
    # Common pytest failure patterns
    patterns = [
        # Standard pytest failure format
        r"(?:FAILED|ERROR)\s+(\S+\.py)::(\S+)",   
        r"(\S+\.py)::(\S+)\s+(?:FAILED|ERROR)",
        # File path in traceback
        r"File \"([^\"]+\.py)\", line \d+",
        # Simple file.py::test format
        r"(\S+\.py)::(\w+)",
    ]
    
    for pat in patterns:
        m = re.search(pat, output)
        if m:
            file = m.group(1)
            test = m.group(2) if len(m.groups()) > 1 else None
            trace = output[-2000:]  # Last 2000 chars for context
            
            print(f"📁 Found failing file: {file}")
            print(f"🧪 Found failing test: {test}")
            
            return {"file": file, "test": test, "trace": trace}

    # If pylint reports a missing import (F0401)
    f_match = re.search(r"(\S+\.py):\d+:\d+: F0401", output)
    if f_match:
        file = f_match.group(1)
        print(f"📁 Found pylint error in file: {file}")
        return {"file": file, "test": None, "trace": output[-2000:]}

    # Look for any Python file mentioned in the output
    py_files = re.findall(r"(\w+\.py)", output)
    if py_files:
        file = py_files[0]  # Take the first one
        print(f"📁 Found Python file in output: {file}")
        return {"file": file, "test": None, "trace": output[-2000:]}

    # Fallback - no specific file found
    print("❌ Could not parse failure - no file identified")
    return {"file": None, "test": None, "trace": output[-2000:]}

def check_test_environment():
    """Check if the test environment is properly set up"""
    try:
        # Check if pytest is available
        proc = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                            capture_output=True, text=True)
        if proc.returncode == 0:
            print(f"✅ pytest available: {proc.stdout.strip()}")
        else:
            print("❌ pytest not available")
            return False
        
        # Check if we're in a git repository
        proc = subprocess.run(["git", "status"], capture_output=True, text=True)
        if proc.returncode == 0:
            print("✅ Git repository detected")
        else:
            print("⚠️  Not in a git repository - patch application may fail")
        
        return True
        
    except Exception as e:
        print(f"❌ Test environment check failed: {e}")
        return False