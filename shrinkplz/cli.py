import shutil
import subprocess
from shrinkplz.output import perr
from shrinkplz.state import SessionStepState
from shrinkplz.mark import cut_input_data, mark_input, MarkResult
import argparse

import os
from pathlib import Path

parser = argparse.ArgumentParser(
    description="""
Bisect your test data to find the smallest size.

During a shrinking session, mark data as passing or
failing. Shrinkplz will shrink down your data as
much as possible until it finds the smallest data
that still causes a test failure.
"""
)

subparsers = parser.add_subparsers(dest="cmd_name")

start_args = subparsers.add_parser("start", help="Start a shrinking session")
start_args.add_argument("file_path")

subparsers.add_parser("abandon", help="Abandon a shrinking session")
mark_args = subparsers.add_parser("mark", help="Mark the current input")
mark_args.add_argument("result", choices=["pass", "fail", "invalid"])

script_args = subparsers.add_parser("script", help="Run a scripted shrinking session")
script_args.add_argument("script_path")
script_args.add_argument("file_path")


SHRINKPLZ_DATA = Path(".shrinkplz")


def save_state(state: SessionStepState):
    with open(SHRINKPLZ_DATA / "current-state", "w") as f:
        state.write_into_file(f)


def read_state() -> SessionStepState:
    with open(SHRINKPLZ_DATA / "current-state", "r") as f:
        return SessionStepState.read_from_file(f)


def mark_cmd(result: MarkResult) -> bool:
    """
    Mark command, returns whether we are 'done'
    """
    try:
        state = read_state()
    except FileNotFoundError:
        perr("Failed to read the state, are we actually in a session?")
        return True
    return mark_input(state, result)


def start_cmd(file_path: str):
    if SHRINKPLZ_DATA.exists():
        perr("A session already exists! Use abandon to get rid of it")
        return 1
    perr("Starting session...")
    with open(file_path, "r") as f:
        initial_data = f.readlines()
    os.mkdir(SHRINKPLZ_DATA)
    with open(SHRINKPLZ_DATA / "current-smallest", "w") as f:
        f.writelines(initial_data)

    initial_line_count = len(initial_data)
    state = SessionStepState(
        bucket_size=initial_line_count // 2,
        cut_idx=0,
        drop_count=0,
        current_smallest=initial_line_count,
    )
    cut_input_data(state.cut_idx, state.bucket_size)
    perr("Wrote first test data to current-input")
    save_state(state)


def script_cmd(file_path, script_path):
    """
    Run everything automatically
    """
    start_cmd(file_path)
    # now to run everything in a loop

    done = False
    while not done:
        result = subprocess.run(script_path)
        if result.returncode == 0:
            done = mark_cmd("pass")
        elif result.returncode == 125:
            done = mark_cmd("invalid")
        else:
            done = mark_cmd("fail")


def main():
    args = parser.parse_args()
    match cmd_name := args.cmd_name:
        case "mark":
            mark_cmd(args.result)
        case "start":
            start_cmd(args.file_path)
        case "abandon":
            shutil.rmtree(SHRINKPLZ_DATA)
            perr("abandoned run")
        case "script":
            script_cmd(args.file_path, args.script_path)
        case None:
            parser.print_help()
        case _:
            # in theory we shouldn't hit this
            raise AssertionError(f"BUG: Unknown command {cmd_name}")
