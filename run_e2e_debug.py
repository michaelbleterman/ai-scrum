#!/usr/bin/env python
"""
Debug wrapper for E2E test that captures and displays actual failure details.
"""
import subprocess
import sys

print("=" * 80)
print("E2E TEST DEBUG RUNNER")
print("=" * 80)

# Run pytest with full output
result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/test_e2e_real.py::TestE2EReal::test_full_lifecycle",
     "-xvs", "--tb=short", "--no-header"],
    capture_output=True,
    text=True,
    cwd=r"C:\Users\Michael\.gemini\.agent"
)

print("\n" + "=" * 80)
print("STDOUT:")
print("=" * 80)
print(result.stdout)

print("\n" + "=" * 80)
print("STDERR:")
print("=" * 80)
print(result.stderr)

print("\n" + "=" * 80)
print(f"EXIT CODE: {result.returncode}")
print("=" * 80)

# Parse and highlight the failure
if result.returncode != 0:
    print("\n" + "!" * 80)
    print("TEST FAILED - Searching for assertion details...")
    print("!" * 80)
    
    output = result.stdout + result.stderr
    
    # Look for common failure patterns
    if "AssertionError" in output:
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "AssertionError" in line or "assert" in line.lower():
                # Print context around assertion
                start = max(0, i - 5)
                end = min(len(lines), i + 10)
                print("\nAssertion context:")
                print("-" * 80)
                for j in range(start, end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{lines[j]}")
                print("-" * 80)
                break
    
    if "FAILED" in output:
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "FAILED" in line:
                print(f"\nFailure line: {line}")
    
    # Look for self.assert calls
    if "self.assert" in output:
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "self.assert" in line:
                print(f"\nAssertion: {line.strip()}")

sys.exit(result.returncode)
