# patcher.py

import tempfile
import subprocess

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"/* error reading {path}: {e} */"

def apply_patch(patch_text: str) -> bool:
    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.write(patch_text)
        tmpname = tf.name
    proc = subprocess.run(["git", "apply", "--index", tmpname], capture_output=True, text=True)
    if proc.returncode != 0:
        print("git apply failed:", proc.stderr)
        return False
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", "Automated fix by LLM"])
    return True
