"""
Pass in a list of failure cases in the first argument

Read in lines.

Return failure if all the failure cases were present
in the input
"""

import sys

with open(sys.argv[1], "r") as f:
    failures = [line.strip() for line in f.readlines()]
in_lines = list(sys.stdin)

has_failed_tests = all(f"{failed_case}\n" in in_lines for failed_case in failures)

if has_failed_tests:
    print("FAILED")
else:
    print("SUCCEEDED")
sys.exit(1 if has_failed_tests else 0)
