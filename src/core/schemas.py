"""HỢP ĐỒNG DỮ LIỆU (schemas) — mọi module cùng phụ thuộc file này và enums.py.
Quy tắc: module KHÔNG import module khác cùng tầng; chỉ trao đổi qua các kiểu ở đây.
Quy ước eval: Score luôn theo góc nhìn TRẮNG. Đổi sang góc nhìn người đi chỉ ở winchance.win_for().
"""
from __future__ import annotations
from dataclasses import dataclass, field
import chess

from src.core.enums import Label


@dataclass(frozen=True)
class Score:
    """Góc nhìn Trắng. Đúng một trong hai: cp hoặc mate (>0: Trắng chiếu hết, <0: Đen chiếu hết)."""
    cp: int | None = None
    mate: int | None = None


@dataclass(frozen=True)
class PVLine:
    rank: int                 # 1-based
    moves: tuple[str, ...]    # UCI, moves[0] là nước đầu của dòng
    score: Score


@dataclass
class PositionAnalysis:
    fen_key: str
    lines: list[PVLine]
    terminal: bool = False    # ván đã kết thúc -> lines rỗng


@dataclass
class MoveEval:
    """Đầu ra của evaluator: toàn bộ số liệu thô của MỘT nước đi. Mọi w_* theo góc nhìn NGƯỜI VỪA ĐI (0-100)."""
    ply: int
    side: chess.Color
    fen_before: str
    move_uci: str
    move_san: str
    book: bool = False
    forced: bool = False
    best_uci: str = ""
    best_san: str = ""
    rank: int = 0                     # 0 = ngoài top multipv
    w_best: float = 50.0
    w_played: float = 50.0
    w_second: float | None = None
    mate_for_mover: bool = False      # dòng 1 là mate có lợi cho người đi
    played_pv: tuple[str, ...] = ()   # PV bắt đầu bằng chính nước đã đi

    @property
    def dwc(self) -> float:
        return min(0.0, self.w_played - self.w_best)

    @property
    def gap12(self) -> float:
        return 0.0 if self.w_second is None else self.w_best - self.w_second


@dataclass
class Hit:
    """Một phát hiện chiến thuật (detector trả về)."""
    name: str
    perspective: str = "EXECUTED"     # EXECUTED | MISSED | THREATENED
    confidence: float = 1.0
    squares: tuple[str, ...] = ()


@dataclass
class Verdict:
    label: Label
    rule: str                         # luật đã kích hoạt, để debug
    dwc: float = 0.0
    sac_value: int = 0
    hits: list[Hit] = field(default_factory=list)
    commentary: str = ""
    nag: int | None = None


@dataclass
class MoveReport:
    eval: MoveEval
    verdict: Verdict


def fen_key(board: chess.Board) -> str:
    """Khóa cache: 4 trường đầu của FEN (bỏ bộ đếm nước)."""
    return " ".join(board.fen().split()[:4])
