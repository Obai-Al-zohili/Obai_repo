#!/usr/bin/env python3
"""
Simple launcher for the bug fixing system
"""

import os
import sys
import subprocess

def main():
    print("🤖 CodeT5 Bug Fixer System")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("best_model.pt"):
        print("❌ Model file not found!")
        print("Make sure you're in the pretrained folder and best_model.pt exists.")
        return
    
    if not os.path.exists("buggy_code.py"):
        print("❌ buggy_code.py not found!")
        print("Make sure buggy_code.py exists in this folder.")
        return
    
    print("✅ All required files found")
    
    # Show menu
    print("\n📋 Available Options:")
    print("1. 🔧 Run automatic bug fixing")
    print("2. 🧪 Test model directly")
    print("3. 📊 Run tests only")
    print("4. 📖 Show current buggy code")
    print("5. ❌ Exit")
    
    while True:
        try:
            choice = input("\n👉 Enter your choice (1-5): ").strip()
            
            if choice == "1":
                print("\n🔧 Running automatic bug fixing...")
                subprocess.run([sys.executable, "auto_fix.py"])
                
            elif choice == "2":
                print("\n🧪 Testing model directly...")
                subprocess.run([sys.executable, "test_model_directly.py"])
                
            elif choice == "3":
                print("\n📊 Running tests only...")
                subprocess.run([sys.executable, "simple_tester.py"])
                
            elif choice == "4":
                print("\n📖 Current buggy code:")
                print("-" * 30)
                try:
                    with open("buggy_code.py", "r") as f:
                        print(f.read())
                except Exception as e:
                    print(f"Error reading file: {e}")
                print("-" * 30)
                
            elif choice == "5":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()