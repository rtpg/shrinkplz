from shutil import copyfile
from typing import Literal
from shrinkplz import SHRINKPLZ_DATA
from shrinkplz.config import Config
from shrinkplz.output import perr
from shrinkplz.state import SessionStepState

type MarkResult = Literal["pass"] | Literal["fail"] | Literal["invalid"]


def mark_result_in_log(state: SessionStepState, result: MarkResult):
    with open(SHRINKPLZ_DATA / "session-log", "a") as f:
        f.write(f"{state.bucket_size},{state.cut_idx},{state.drop_count},{result}\n")


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
    if state.looks_completed():
        copyfile(SHRINKPLZ_DATA / "current-smallest", "current-input")
        perr(
            """
Completed our search!
The smallest known data is copied
to current-input
"""
        )
        return True
    save_state(state)
    # let's prepare the current-input
    cut_input_data(state.cut_idx, state.bucket_size)
    perr("Smallest failed test data written to current-input")
    return False


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


def save_state(state: SessionStepState):
    with open(SHRINKPLZ_DATA / "current-state", "w") as f:
        state.write_into_file(f)


def read_state() -> SessionStepState:
    with open(SHRINKPLZ_DATA / "current-state", "r") as f:
        return SessionStepState.read_from_file(f)


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
