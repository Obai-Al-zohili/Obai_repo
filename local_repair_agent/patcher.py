# patcher.py

import tempfile
import subprocess
import os

def read_file(path: str) -> str:
    """Read file contents with error handling"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"/* error reading {path}: {e} */"

def apply_patch(patch_text: str) -> bool:
    """Apply a unified diff patch using git apply"""
    if not patch_text.strip():
        print("❌ Empty patch provided")
        return False
    
    # Create temporary patch file
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".patch", encoding="utf-8") as tf:
        tf.write(patch_text)
        tmpname = tf.name
    
    try:
        print(f"📝 Applying patch from: {tmpname}")
        
        # Try to apply the patch with git apply
        proc = subprocess.run(
            ["git", "apply", "--index", tmpname], 
            capture_output=True, 
            text=True,
            cwd="."
        )
        
        if proc.returncode != 0:
            print(f"❌ git apply failed (return code: {proc.returncode})")
            print(f"stderr: {proc.stderr}")
            print(f"stdout: {proc.stdout}")
            print("📋 Patch content:")
            print(patch_text)
            
            # Try without --index flag as fallback
            print("🔄 Trying without --index flag...")
            proc2 = subprocess.run(
                ["git", "apply", tmpname], 
                capture_output=True, 
                text=True,
                cwd="."
            )
            
            if proc2.returncode != 0:
                print(f"❌ git apply (without --index) also failed: {proc2.stderr}")
                return False
            else:
                print("✅ Patch applied successfully (without --index)")
        else:
            print("✅ Patch applied successfully")
        
        # Stage and commit the changes
        print("📦 Staging changes...")
        stage_proc = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
        if stage_proc.returncode != 0:
            print(f"⚠️  Git add warning: {stage_proc.stderr}")
        
        print("💾 Committing changes...")
        commit_proc = subprocess.run(
            ["git", "commit", "-m", "Automated fix by Local Model"], 
            capture_output=True, 
            text=True
        )
        
        if commit_proc.returncode != 0:
            print(f"⚠️  Git commit warning: {commit_proc.stderr}")
            # This might not be an error if there are no changes to commit
            if "nothing to commit" in commit_proc.stdout:
                print("ℹ️  No changes to commit")
            else:
                print("⚠️  Commit failed, but patch was applied")
        else:
            print("✅ Changes committed successfully")
            
        return True
        
    except Exception as e:
        print(f"❌ Patch application failed with exception: {e}")
        return False
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmpname)
        except Exception as e:
            print(f"⚠️  Could not clean up temp file {tmpname}: {e}")

def write_file(path: str, content: str) -> bool:
    """Write content to file with error handling"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ File written: {path}")
        return True
    except Exception as e:
        print(f"❌ Error writing file {path}: {e}")
        return False