"""Keo dán: Core -> Engine -> Analyzer. Không import pgn_io (main.py làm việc đó) và không import detectors
(Phase 2 cắm vào qua tham số find_hits)."""
from __future__ import annotations
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Thread
from typing import TYPE_CHECKING, Callable
import warnings
import chess, chess.pgn
from src.analyzer.classifier import classify
from src.analyzer.evaluator import Evaluator
from src.analyzer.scheduler import is_hot
from src.analyzer.text_generator import make_comment
from src.core.config import NAG_MAP, Config
from src.core.schemas import Hit, MoveEval, MoveReport, Verdict
from src.primitives.pv_tools import summarize_pv

if TYPE_CHECKING:
    from src.engine.engine_pool import EnginePool

IsBook = Callable[[chess.Board, chess.Move], bool]
FindHits = Callable[[chess.Board, chess.Move, MoveEval], list[Hit]]


@dataclass(frozen=True)
class HotTask:
    """Nhiệm vụ đào sâu cho một nước đi hot."""
    ply: int
    board: chess.Board
    move: chess.Move
    sac_fast: int


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


def analyse_game_parallel(
    game: chess.pgn.Game,
    engine_pool: EnginePool,
    cfg: Config = Config(),
    is_book: IsBook | None = None,
    find_hits: FindHits | None = None,
) -> list[MoveReport]:
    """Phân tích ván cờ song song 2 lượt (two-pass) với 2 Stockfish instances.

    - Phase 1: SF1 (scanner) quét nhanh toàn ván. Nước nào is_hot() đẩy vào hot_queue.
               SF2 (hot_worker) chạy ngầm trong background thread, liên tục lấy nước hot từ queue để đào sâu.
    - Phase 2: Sau khi quét nhanh xong toàn bộ ván, SF1 không ngồi chờ mà nhảy vào phụ SF2 (work-stealing)
               lấy nốt các task còn lại trong queue cho đến khi rỗng.
    - Phase 3: Gộp kết quả (deep_evals ưu tiên hơn fast_evals), tính sac, chạy classify, tạo Verdict và MoveReport.
    """
    if not cfg.two_pass:
        warnings.warn(
            "analyse_game_parallel được gọi nhưng cfg.two_pass=False. "
            "Tự động fallback sang analyse_game tuần tự với engine scanner."
        )
        evaluator = Evaluator(engine_pool.scanner, cfg)
        return analyse_game(game, evaluator, cfg, is_book, find_hits)

    fast_eval = Evaluator(engine_pool.scanner, cfg)
    worker_eval = Evaluator(engine_pool.hot_worker, cfg)

    hot_queue: Queue[HotTask | None] = Queue()
    fast_evals: dict[int, MoveEval] = {}
    deep_evals: dict[int, MoveEval] = {}
    boards_by_ply: dict[int, chess.Board] = {}
    moves_by_ply: dict[int, chess.Move] = {}
    books_by_ply: dict[int, bool] = {}

    worker_exc: Exception | None = None

    def hot_worker_loop() -> None:
        nonlocal worker_exc
        try:
            while True:
                item = hot_queue.get()
                if item is None:
                    hot_queue.task_done()
                    break
                try:
                    deep_evals[item.ply] = worker_eval.evaluate_move(
                        item.board, item.move, item.ply,
                        depth=cfg.depth, multipv=cfg.multipv
                    )
                finally:
                    hot_queue.task_done()
        except Exception as e:
            worker_exc = e

    worker_thread = Thread(target=hot_worker_loop, daemon=True)
    worker_thread.start()

    try:
        # Phase 1: SF1 quét nhanh toàn ván cờ
        board = game.board()
        in_book = is_book is not None

        for ply, node in enumerate(game.mainline(), 1):
            move = node.move
            book = in_book and is_book(board, move)
            in_book = book

            boards_by_ply[ply] = board.copy(stack=False)
            moves_by_ply[ply] = move
            books_by_ply[ply] = book

            if book:
                ev = fast_eval.evaluate_move(board, move, ply, book=True)
                fast_evals[ply] = ev
            else:
                ev = fast_eval.evaluate_move(
                    board, move, ply, book=False,
                    depth=cfg.fast_depth, multipv=cfg.fast_multipv
                )
                fast_evals[ply] = ev
                sac = _sac(board, ev, cfg)
                if is_hot(ev, sac, cfg):
                    hot_queue.put(HotTask(ply, board.copy(stack=False), move, sac))

            board.push(move)

        # Phase 2: Work-stealing — SF1 nhảy vào giải phóng các task còn lại trong hot_queue
        while True:
            try:
                item = hot_queue.get_nowait()
            except Empty:
                break
            if item is None:
                hot_queue.put(None)
                break
            try:
                deep_evals[item.ply] = fast_eval.evaluate_move(
                    item.board, item.move, item.ply,
                    depth=cfg.depth, multipv=cfg.multipv
                )
            finally:
                hot_queue.task_done()

    finally:
        # Báo hiệu worker thread dừng và chờ thread hoàn tất
        hot_queue.put(None)
        worker_thread.join()

    if worker_exc is not None:
        raise worker_exc

    # Phase 3: Gộp kết quả và phân loại
    reports: list[MoveReport] = []
    total_plies = len(fast_evals)
    for ply in range(1, total_plies + 1):
        board_at_ply = boards_by_ply[ply]
        move = moves_by_ply[ply]
        book = books_by_ply[ply]

        ev = deep_evals.get(ply, fast_evals[ply])
        sac, hits = 0, []
        if not book:
            sac = _sac(board_at_ply, ev, cfg)
            if find_hits:
                hits = find_hits(board_at_ply.copy(stack=False), move, ev)

        label, rule = classify(ev, cfg, sac)
        v = Verdict(label, rule, ev.dwc, sac, hits, nag=NAG_MAP.get(label))
        v.commentary = make_comment(ev, v)
        reports.append(MoveReport(ev, v))

    return reports
