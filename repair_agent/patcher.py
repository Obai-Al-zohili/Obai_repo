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
    # Use git apply for all patches
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".patch") as tf:
        tf.write(patch_text)
        tmpname = tf.name
    
    try:
        # Try to apply the patch
        proc = subprocess.run(["git", "apply", "--index", tmpname], capture_output=True, text=True)
        if proc.returncode != 0:
            print("git apply failed:", proc.stderr)
            print("Patch content:")
            print(patch_text)
            return False
        
        # Stage and commit the changes
        subprocess.run(["git", "add", "-A"])
        result = subprocess.run(["git", "commit", "-m", "Automated fix by LLM"], capture_output=True, text=True)
        if result.returncode != 0:
            print("Git commit failed:", result.stderr)
            return False
            
        return True
    except Exception as e:
        print(f"Patch application failed: {e}")
        return False
    finally:
        # Clean up temporary file
        try:
            import os
            os.unlink(tmpname)
        except:
            pass
