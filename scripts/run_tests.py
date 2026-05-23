import os
import sys
import importlib.util
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_test_file(filepath):
    print(f"Running tests in {os.path.basename(filepath)}...")
    spec = importlib.util.spec_from_file_location("test_module", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    test_functions = [getattr(module, attr) for attr in dir(module) if attr.startswith("test_") and callable(getattr(module, attr))]
    
    passed = 0
    failed = 0
    for func in test_functions:
        try:
            func()
            print(f"  [PASS] {func.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            
    print(f"Summary for {os.path.basename(filepath)}: {passed} passed, {failed} failed\n")
    return passed, failed

if __name__ == "__main__":
    test_files = [
        "tests/test_scoring.py",
        "tests/test_drafts.py",
        "tests/test_org.py"
    ]
    
    total_passed = 0
    total_failed = 0
    for f in test_files:
        if os.path.exists(f):
            p, fl = run_test_file(f)
            total_passed += p
            total_failed += fl
            
    print(f"Global Summary: {total_passed} passed, {total_failed} failed")
    if total_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)
