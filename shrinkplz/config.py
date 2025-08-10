from dataclasses import dataclass


@dataclass
class Config:
    """
    Config state of the shrinkplz run
    """

    # The minimimum size of a test, we'll consider shrinking done at this point
    min_test_size: int
