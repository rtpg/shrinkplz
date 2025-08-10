import subprocess
import tempfile
import pytest
from pathlib import Path
import shutil
import os

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

proj_root = Path(__file__).parent.parent


@pytest.fixture
def temp_dir():
    """
    Fixture that provides a TempDirectory instance with automatic cleanup.
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def run_shrinkplz():
    """
    Fixture that provides a helper functon to run shrinkplz commands.
    """

    def _run_command(args, cwd=None, input_data=None):
        """
        Run shrinkplz command with given arguments.

        Args:
            args: List of command line arguments (without 'shrinkplz')
            cwd: Working directory to run command in
            input_data: Data to pass to stdin

        Returns:
            subprocess.CompletedProcess result
        """
        cmd = ["uv", "run", "shrinkplz"] + args
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, input=input_data
        )
        return result

    return _run_command


class ScriptSession:
    """
    A shrinkplz script session
    """

    def __init__(self, temp_dir: Path) -> None:
        self.temp_dir = temp_dir

        # copy over the test prog and the test script
        shutil.copy(proj_root / "example" / "my-prog.py", self.temp_dir / "my-prog.py")
        shutil.copy(
            proj_root / "example" / "my-test-script", self.temp_dir / "my-test-script"
        )

    def set_failure_cases(self, cases: str) -> None:
        """
        Set the failure cases for this session
        (one char turns into one line)
        """
        with open(self.temp_dir / "failure-cases", "w") as f:
            f.writelines([f"{c}\n" for c in cases])

    def set_starting_input(self, start: str) -> None:
        """
        Set our starting input
        (one char turns into one line)
        """
        with open(self.temp_dir / "starting-test-input", "w") as f:
            f.writelines([f"{c}\n" for c in start])

    def run(
        self, args: list[str] | None = None
    ) -> tuple[subprocess.CompletedProcess, list[str]]:
        # TODO I should just call the command directly...

        if args is None:
            args = []
        cmd = (
            ["uv", "run", "shrinkplz"]
            + args
            + ["script", "./my-test-script", "./starting-test-input"]
        )
        result = subprocess.run(
            cmd,
            cwd=self.temp_dir,
            text=True,
        )

        assert result.returncode == 0

        final_lines = [
            line.strip()
            for line in open(self.temp_dir / "current-input", "r").readlines()
        ]

        return final_lines


@pytest.fixture
def session(temp_dir):
    yield ScriptSession(temp_dir)


def test_shrinkplz_script_session(session: ScriptSession):
    """
    Test shrinkplz script session using the example data.
    """

    session.set_failure_cases("DUVX")
    session.set_starting_input(ALPHABET)

    final_lines = session.run()

    assert final_lines == ["D", "U", "V", "X"]


def test_minimum_size_session(session: ScriptSession):
    session.set_failure_cases("DUVX")
    session.set_starting_input(ALPHABET)

    final_lines = session.run(["--min-test-size", "6"])

    assert len(final_lines) == 6
    # but we should have our failures!
    assert {"D", "U", "V", "X"}.issubset(set(final_lines))
