# main.py

import config
from tester import run_tests, parse_failure
from patcher import read_file, apply_patch
from model_client import call_llm_propose_patch


def main():
    print("🚀 Starting Local Model Repair Agent")
    print(f"📍 Model: {config.BASE_MODEL}")
    print(f"📦 Weights: {config.FINETUNED_WEIGHTS}")
    print(f"🔧 Device: {config.DEVICE}")
    print("=" * 50)

    for i in range(1, config.MAX_ITER + 1):
        print(f"\n=== Iteration {i} ===")

        passed, output = run_tests()
        if passed:
            print("✅ All tests passed")
            return

        info = parse_failure(output)
        if not info["file"]:
            print("❌ Could not identify failing file")
            return

        file_path = info["file"]
        contents = read_file(file_path)

        patch = call_llm_propose_patch(
            file_path,
            contents,
            info["test"],
            info["trace"],
        )

        if not patch.strip():
            print("⚠️ No patch generated — stopping")
            return

        print("📋 Applying patch...")
        if not apply_patch(patch):
            print("❌ Patch failed")
            return

    print("⏰ Max iterations reached")


if __name__ == "__main__":
    main()
