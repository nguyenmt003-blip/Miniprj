"""Keo dán: Core -> Engine -> Analyzer. Không import pgn_io (main.py làm việc đó) và không import detectors
(Phase 2 cắm vào qua tham số find_hits)."""
from __future__ import annotations
from typing import Callable
import chess, chess.pgn
from src.analyzer.classifier import classify
from src.analyzer.evaluator import Evaluator
from src.analyzer.scheduler import is_hot
from src.analyzer.text_generator import make_comment
from src.core.config import NAG_MAP, Config
from src.core.schemas import Hit, MoveEval, MoveReport, Verdict
from src.primitives.pv_tools import summarize_pv

IsBook = Callable[[chess.Board, chess.Move], bool]
FindHits = Callable[[chess.Board, chess.Move, MoveEval], list[Hit]]


def _sac(board: chess.Board, ev: MoveEval, cfg: Config) -> int:
    return max(0, -summarize_pv(board, ev.played_pv, board.turn, cfg.pv_plies).net_at_leaf) if ev.played_pv else 0


def _evaluate(evaluator: Evaluator, board, move, ply, book, cfg) -> MoveEval:
    if book or not cfg.two_pass:
        return evaluator.evaluate_move(board, move, ply, book)
    ev = evaluator.evaluate_move(board, move, ply, depth=cfg.fast_depth, multipv=cfg.fast_multipv)   # lượt 1
    if is_hot(ev, _sac(board, ev, cfg), cfg):
        ev = evaluator.evaluate_move(board, move, ply)                                              # lượt 2: sâu
    return ev


def analyse_game(game: chess.pgn.Game, evaluator: Evaluator, cfg: Config = Config(),
                 is_book: IsBook | None = None, find_hits: FindHits | None = None) -> list[MoveReport]:
    board, reports = game.board(), []
    in_book = is_book is not None
    for ply, node in enumerate(game.mainline(), 1):
        move = node.move
        book = in_book and is_book(board, move)
        in_book = book                                  # lệch sách một lần là hết sách
        ev = _evaluate(evaluator, board, move, ply, book, cfg)
        sac, hits = 0, []
        if not book:
            sac = _sac(board, ev, cfg)
            if find_hits:
                hits = find_hits(board.copy(stack=False), move, ev)
        label, rule = classify(ev, cfg, sac)
        v = Verdict(label, rule, ev.dwc, sac, hits, nag=NAG_MAP.get(label))
        v.commentary = make_comment(ev, v)
        reports.append(MoveReport(ev, v))
        board.push(move)
    return reports
