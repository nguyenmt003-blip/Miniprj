"""Module 1 — toán thuần. Đây là NƠI DUY NHẤT đổi góc nhìn Trắng -> người đi."""
import math
import chess
from src.core.schemas import Score


def cp_to_win(cp: float) -> float:
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def win_white(s: Score) -> float:
    if s.mate is not None:
        return 100.0 if s.mate > 0 else 0.0
    return cp_to_win(s.cp or 0)


def win_for(s: Score, color: chess.Color) -> float:
    w = win_white(s)
    return w if color == chess.WHITE else 100.0 - w
