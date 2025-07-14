from shutil import copyfile
import shutil
from typing import Literal
import subprocess
from shrinkplz.state import SessionStepState
import argparse

import os
from pathlib import Path

parser = argparse.ArgumentParser(
    description="""
Help shrink test data

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


def cut_input_data(cut_idx: int, bucket_size: int):
    """
    Given our state, cut the input data, holding onto the cut data
    in a pending-drop file

    reads current-smallest, generates pending-drop and current-input
    """
    # this is not very smart
    with open(SHRINKPLZ_DATA / "current-smallest", "r") as f:
        current_smallest = f.readlines()
    # split out the data

    # first, we have our pending drop
    pending_drop = current_smallest[cut_idx : cut_idx + bucket_size]
    with open(SHRINKPLZ_DATA / "pending-drop", "w") as f:
        f.writelines(pending_drop)

    # then we build out our current input
    current_input = (
        current_smallest[:cut_idx] + current_smallest[cut_idx + bucket_size :]
    )

    # XXX current-input target
    with open("current-input", "w") as f:
        f.writelines(current_input)


def commit_pending_drop(cut_idx: int, bucket_size: int) -> int:
    """
    Commit the pending drop on the current-smallest file
    """
    # We redo the logic to generate the current-input instead of copying it
    # to avoid issues with current-input being written to
    with open(SHRINKPLZ_DATA / "current-smallest", "r") as f:
        current_smallest = f.readlines()
    shrunk = current_smallest[:cut_idx] + current_smallest[cut_idx + bucket_size :]
    new_linecount = len(shrunk)
    with open(SHRINKPLZ_DATA / "current-smallest", "w") as f:
        f.writelines(shrunk)

    return new_linecount


type MarkResult = Literal["pass"] | Literal["fail"] | Literal["invalid"]


def mark_result_in_log(state: SessionStepState, result: MarkResult):
    with open(SHRINKPLZ_DATA / "session-log", "a") as f:
        f.write(f"{state.bucket_size},{state.cut_idx},{state.drop_count},{result}\n")


def save_state(state: SessionStepState):
    with open(SHRINKPLZ_DATA / "current-state", "w") as f:
        state.write_into_file(f)


def read_state() -> SessionStepState:
    with open(SHRINKPLZ_DATA / "current-state", "r") as f:
        return SessionStepState.read_from_file(f)


def progress_state_if_needed(state: SessionStepState):
    """
    Check to see if we are beyond the end of our data

    if so, we should shrink the bucket size and go to
    the beginning.
    """
    if state.cut_idx >= state.current_smallest:
        state.cut_idx = 0
        state.bucket_size //= 2
        state.drop_count = 0


def mark_input(state: SessionStepState, result: MarkResult) -> bool:
    """
    Mark some input

    returns whether we are "done"
    """
    mark_result_in_log(state, result)
    match result:
        case "pass":
            # if we passed that means the cut data was important
            # so we're going to re-insert it, then move the cut_idx forward
            state.cut_idx += state.bucket_size
        case "fail":
            # if we fail, that means we're in a good spot
            # we can discard it and increment the drop_count
            state.drop_count += 1
            new_linecount = commit_pending_drop(state.cut_idx, state.bucket_size)
            state.current_smallest = new_linecount
        case "invalid":
            # if we have invalid data we can't say whether we're in
            # a good state or not, so we'll just move the cut_idx forward
            state.cut_idx += state.bucket_size

    progress_state_if_needed(state)
    if state.bucket_size == 0:
        copyfile(SHRINKPLZ_DATA / "current-smallest", "current-input")
        print(
            """
Completed our search!
The smallest known data is copied
to current-input
"""
        )
        return True
    print(state)
    save_state(state)
    # let's prepare the current-input
    cut_input_data(state.cut_idx, state.bucket_size)
    print("New data available at current-input")
    return False


def mark_cmd(result: MarkResult) -> bool:
    """
    Mark command, returns whether we are 'done'
    """
    try:
        state = read_state()
    except FileNotFoundError:
        print("Failed to read the state, are we actually in a session?")
        return True
    return mark_input(state, result)


def start_cmd(file_path: str):
    if SHRINKPLZ_DATA.exists():
        print("A session already exists! Use abandon to get rid of it")
        return
    print("Starting session...")
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
    print("Wrote first test data to current-input")
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
            print("abandoned run")
        case "script":
            script_cmd(args.file_path, args.script_path)
        case _:
            raise AssertionError(f"Unknown command {cmd_name}")
