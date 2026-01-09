#!/usr/bin/env python3
# test_setup.py - Test script to verify local repair agent setup

import os
import sys
import torch
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking Local Repair Agent Setup")
    print("=" * 50)
    
    issues = []
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version < (3, 8):
        issues.append("Python 3.8+ required")
    
    # Check required packages
    required_packages = ['torch', 'transformers', 'pytest']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Available")
        except ImportError:
            print(f"❌ {package}: Missing")
            issues.append(f"Missing package: {package}")
    
    # Check model file
    model_path = "../best_model.pt"
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✅ Model file: {model_path} ({size_mb:.1f} MB)")
    else:
        print(f"❌ Model file: {model_path} not found")
        issues.append("Model file missing")
    
    # Check CUDA availability
    if torch.cuda.is_available():
        print(f"✅ CUDA: Available (GPU: {torch.cuda.get_device_name()})")
    else:
        print("⚠️  CUDA: Not available (will use CPU)")
    
    # Check git
    try:
        import subprocess
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git: {result.stdout.strip()}")
        else:
            print("❌ Git: Not working")
            issues.append("Git not available")
    except FileNotFoundError:
        print("❌ Git: Not installed")
        issues.append("Git not installed")
    
    # Check if in git repository
    if os.path.exists('.git') or os.path.exists('../.git'):
        print("✅ Git repository: Detected")
    else:
        print("⚠️  Git repository: Not detected (patches may fail)")
        issues.append("Not in git repository")
    
    print("\n" + "=" * 50)
    
    if issues:
        print("❌ Setup Issues Found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n💡 Fix these issues before running the repair agent")
        return False
    else:
        print("✅ All checks passed! Ready to run repair agent")
        return True

def test_model_loading():
    """Test if the model can be loaded successfully"""
    print("\n🧠 Testing Model Loading")
    print("-" * 30)
    
    try:
        from model_client import LocalModelClient
        
        print("📦 Loading model...")
        client = LocalModelClient()
        
        print("🧪 Testing inference...")
        test_code = "def add(a, b):\n    return a + b"
        result = client.generate_fix(test_code)
        
        print(f"✅ Model test successful!")
        print(f"📝 Test input: {test_code}")
        print(f"📝 Test output: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False

if __name__ == "__main__":
    setup_ok = check_requirements()
    
    if setup_ok:
        model_ok = test_model_loading()
        
        if model_ok:
            print("\n🚀 Setup complete! You can now run:")
            print("   python main.py")
        else:
            print("\n❌ Model loading failed. Check the error above.")
    else:
        print("\n❌ Setup incomplete. Fix the issues above first.")