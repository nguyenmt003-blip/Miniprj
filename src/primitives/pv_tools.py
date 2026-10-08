"""Duyệt một PV và đo vật chất dọc đường (nền tảng của phát hiện thí quân)."""
from __future__ import annotations
from dataclasses import dataclass
import chess
from src.primitives.material import balance


@dataclass(frozen=True)
class PVMaterial:
    net_at_leaf: int      # thay đổi vật chất của người đi tại lá yên tĩnh (âm = đang thí)
    peak_deficit: int     # mức hụt lớn nhất dọc đường
    leaf_ply: int


def summarize_pv(board: chess.Board, pv: tuple[str, ...], mover: chess.Color, max_plies: int = 8) -> PVMaterial:
    """Đi theo PV; lá yên tĩnh = ply đầu tiên mà nước kế tiếp không phải ăn quân."""
    b = board.copy(stack=False)
    start = balance(b, mover)
    lowest, k = start, 0
    limit = min(len(pv), max_plies)
    while k < limit:
        b.push(chess.Move.from_uci(pv[k])); k += 1
        lowest = min(lowest, balance(b, mover))
        if k >= len(pv) or not b.is_capture(chess.Move.from_uci(pv[k])):
            break
    return PVMaterial(balance(b, mover) - start, max(0, start - lowest), k)
