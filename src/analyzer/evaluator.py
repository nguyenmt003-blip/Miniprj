"""Module 4 — biến (board, move) thành MoveEval. Engine chỉ chạy 1 lần/thế cờ (cache theo FEN)."""
from __future__ import annotations
import chess
from src.core.config import Config
from src.core.schemas import MoveEval, PositionAnalysis, Score, fen_key
from src.engine.protocol import Engine
from src.core.winchance import win_for


def terminal_score(board: chess.Board) -> Score:
    """Chiếu hết: 'mate in 0' mất thông tin dấu nên lưu ±1. Hòa/ván kết thúc khác: 0."""
    if board.is_checkmate():
        return Score(mate=1 if board.turn == chess.BLACK else -1)   # bên bị chiếu hết là board.turn
    return Score(cp=0)


class Evaluator:
    def __init__(self, engine: Engine, cfg: Config = Config()):
        self.engine, self.cfg = engine, cfg
        self._cache: dict[tuple, PositionAnalysis] = {}

    def analyse(self, board: chess.Board, depth: int | None = None, multipv: int | None = None) -> PositionAnalysis:
        depth, multipv = depth or self.cfg.depth, multipv or self.cfg.multipv
        fk = fen_key(board)
        key = (fk, depth, multipv)          # cache theo (thế, depth, multipv): không bao giờ trộn depth khác nhau
        if key not in self._cache:
            if board.is_game_over():
                self._cache[key] = PositionAnalysis(fk, [], terminal=True)
            else:
                lines = self.engine.analyse(board, multipv, depth)
                if not lines or not lines[0].moves:
                    raise RuntimeError(f"Engine không trả PV cho {fk}")
                self._cache[key] = PositionAnalysis(fk, lines)
        return self._cache[key]

    def evaluate_move(self, board: chess.Board, move: chess.Move, ply: int, book: bool = False,
                      depth: int | None = None, multipv: int | None = None) -> MoveEval:
        mover, uci = board.turn, move.uci()
        ev = MoveEval(ply, mover, board.fen(), uci, board.san(move), book=book)
        if book:
            return ev
        ev.forced = board.legal_moves.count() == 1
        lines = self.analyse(board, depth, multipv).lines
        best = lines[0]
        ev.best_uci = best.moves[0]
        ev.best_san = board.san(chess.Move.from_uci(ev.best_uci))
        ev.w_best = win_for(best.score, mover)
        if len(lines) > 1:
            ev.w_second = win_for(lines[1].score, mover)
        if best.score.mate is not None:
            ev.mate_for_mover = (best.score.mate > 0) == (mover == chess.WHITE)

        ev.rank = next((l.rank for l in lines if l.moves[0] == uci), 0)
        if ev.rank:
            line = lines[ev.rank - 1]
            ev.w_played, ev.played_pv = win_for(line.score, mover), line.moves
        else:   # ngoài top: lấy dòng 1 của thế SAU nước đi (đã ở góc nhìn Trắng, nên không cần đảo thêm)
            after = board.copy(stack=False); after.push(move)
            pa = self.analyse(after, depth, multipv)   # cùng depth với thế trước
            if pa.terminal:
                score, pv = terminal_score(after), (uci,)
            else:
                score, pv = pa.lines[0].score, (uci,) + pa.lines[0].moves
            ev.w_played, ev.played_pv = win_for(score, mover), pv
        return ev
