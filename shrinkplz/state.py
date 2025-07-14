from dataclasses import dataclass
import io


@dataclass
class SessionStepState:
    """
    This is the state of the current session
    """

    # the size of an individual bucket
    bucket_size: int
    # the current index in the file where we should cut
    # next (or where we should re-insert cut data)
    cut_idx: int
    # the number of drops we've done at this bucket size
    drop_count: int
    # the size of our current-smallest data
    current_smallest: int

    @staticmethod
    def read_from_file(f: io.FileIO) -> "SessionStepState":
        bucket_size = int(f.readline())
        cut_idx = int(f.readline())
        drop_count = int(f.readline())
        current_smallest = int(f.readline())
        return SessionStepState(
            bucket_size=bucket_size,
            cut_idx=cut_idx,
            drop_count=drop_count,
            current_smallest=current_smallest,
        )

    def write_into_file(self, f: io.FileIO) -> "SessionStepState":
        for line in [
            str(self.bucket_size),
            str(self.cut_idx),
            str(self.drop_count),
            str(self.current_smallest),
        ]:
            f.write(f"{line}\n")
