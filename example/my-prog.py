"""
My program, that fails when I have D + U + V + W in the set
"""

import sys

failures = ["D", "U", "V", "W"]
in_lines = list(sys.stdin)

has_failed_tests = all(f"{failed_case}\n" in in_lines for failed_case in failures)

if has_failed_tests:
    print("FAILED")
    sys.exit(1)
else:
    print("SUCCEEDED")
sys.exit(1 if has_failed_tests else 0)
