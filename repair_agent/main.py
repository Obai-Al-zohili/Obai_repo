# main.py

import config
from tester import run_tests, parse_failure
from patcher import read_file, apply_patch
from llm_client import call_llm_propose_patch

def main():
    for it in range(1, config.MAX_ITER + 1):
        print(f"=== Iteration {it} ===")
        passed, out = run_tests()
        if passed:
            print("All tests passed ✅")
            return
        info = parse_failure(out)
        if not info.get("file"):
            print("Could not locate failing file. Trace:\n", out)
            return
        fpath = info["file"]
        ft   = info["test"]
        trace= info["trace"]
        print("Failing file:", fpath, "test:", ft)
        contents = read_file(fpath)
        try:
            patch = call_llm_propose_patch(fpath, contents, ft, trace)
        except Exception as e:
            print("Error calling LLM:", e)
            return
        print("Patch obtained:")
        print(patch)
        ok = apply_patch(patch)
        if not ok:
            print("Patch application failed; stopping.")
            return
    print("Reached max iterations. Stopping.")

if __name__ == "__main__":
    main()
