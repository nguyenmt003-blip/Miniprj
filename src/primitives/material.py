"""Đếm vật chất."""
import chess

VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def balance(board: chess.Board, color: chess.Color) -> int:
    def side(c): return sum(v * len(board.pieces(p, c)) for p, v in VALUES.items())
    return side(color) - side(not color)
