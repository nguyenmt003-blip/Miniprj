"""Các enum dùng chung."""
from enum import Enum


class Label(str, Enum):
    BOOK = "BOOK"; FORCED = "FORCED"; BRILLIANT = "BRILLIANT"; GREAT = "GREAT"
    BEST = "BEST"; EXCELLENT = "EXCELLENT"; GOOD = "GOOD"; INTERESTING = "INTERESTING"
    INACCURACY = "INACCURACY"; MISTAKE = "MISTAKE"; MISS = "MISS"; BLUNDER = "BLUNDER"
