"""Tests for parallel analysis pipeline (TICKET-06)."""
from __future__ import annotations

import ctypes
import io
from pathlib import Path
import sys
import time
import chess.pgn
import pytest

from src.analyzer.evaluator import Evaluator
from src.analyzer.pipeline import analyse_game, analyse_game_parallel
from src.core.config import Config
from src.core.enums import Label
from src.core.schemas import MoveReport
from src.engine.engine_pool import EnginePool
from src.engine.stockfish_client import StockfishEngine
from src.pgn_io.pgn_handler import read_games


def find_stockfish() -> Path | None:
    """Tự động phát hiện đường dẫn Stockfish tại data/engines/stockfish.exe."""
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "data" / "engines" / "stockfish.exe",
        root / "data" / "engines" / "stockfish",
        Path("data/engines/stockfish.exe").resolve(),
        Path("data/engines/stockfish").resolve(),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def find_opera_game() -> Path | None:
    """Tự động phát hiện đường dẫn opera_game.pgn tại input_pgn/opera_game.pgn."""
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "input_pgn" / "opera_game.pgn",
        Path("input_pgn/opera_game.pgn").resolve(),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


STOCKFISH_PATH = find_stockfish()
OPERA_PATH = find_opera_game()

require_stockfish = pytest.mark.skipif(
    STOCKFISH_PATH is None,
    reason="Stockfish binary not found at data/engines/stockfish.exe",
)
require_opera = pytest.mark.skipif(
    OPERA_PATH is None,
    reason="opera_game.pgn not found at input_pgn/opera_game.pgn",
)


def _is_pid_alive(pid: int) -> bool:
    """Kiểm tra xem PID còn đang hoạt động ở mức hệ điều hành hay không."""
    if sys.platform == "win32":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid
        )
        if not handle:
            return False
        try:
            res = ctypes.windll.kernel32.WaitForSingleObject(handle, 0)
            return res != 0
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    else:
        try:
            import os
            os.kill(pid, 0)
            return True
        except OSError:
            return False


@pytest.fixture(scope="module")
def opera_analysis_results():
    """Chạy phân tích opera_game.pgn cả tuần tự và song song một lần để chia sẻ giữa các test."""
    if STOCKFISH_PATH is None or OPERA_PATH is None:
        pytest.skip("Stockfish hoặc opera_game.pgn không khả dụng.")

    cfg_seq = Config(two_pass=True, parallel=False, fast_depth=14, depth=20)
    cfg_par = Config(two_pass=True, parallel=True, fast_depth=14, depth=20)

    # 1. Chạy tuần tự và đo thời gian
    game_seq = next(read_games(str(OPERA_PATH)))
    t0 = time.perf_counter()
    with StockfishEngine(str(STOCKFISH_PATH), cfg_seq) as eng:
        ev = Evaluator(eng, cfg_seq)
        seq_reports = analyse_game(game_seq, ev, cfg_seq)
    seq_time = time.perf_counter() - t0

    # 2. Chạy song song và đo thời gian
    game_par = next(read_games(str(OPERA_PATH)))
    t1 = time.perf_counter()
    with EnginePool(str(STOCKFISH_PATH), cfg_par) as pool:
        par_reports = analyse_game_parallel(game_par, pool, cfg_par)
    par_time = time.perf_counter() - t1

    return seq_reports, par_reports, seq_time, par_time


@require_stockfish
@require_opera
def test_parallel_labels_match_sequential(opera_analysis_results):
    """Dùng opera_game.pgn, so sánh danh sách Label của từng nước giữa hai mode."""
    seq_reports, par_reports, _, _ = opera_analysis_results
    assert len(seq_reports) == len(par_reports) == 33

    seq_labels = [r.verdict.label for r in seq_reports]
    par_labels = [r.verdict.label for r in par_reports]

    # Kiểm tra tính tương đương nhãn phân loại:
    # 1. Tỷ lệ khớp nhãn >= 80% (sai số nhỏ do bảng chuyển vị Stockfish độc lập giữa các tiến trình)
    matches = sum(1 for s, p in zip(seq_labels, par_labels) if s == p)
    match_rate = matches / len(seq_labels)
    assert match_rate >= 0.80, f"Tỷ lệ khớp nhãn không đạt yêu cầu tương đương: {match_rate:.2%} ({matches}/{len(seq_labels)})"

    # 2. Các nước then chốt (Brilliant Morphy ply 31, Forced ply 32, Great ply 33) phải hoàn toàn nhất quán
    assert seq_labels[30] == Label.BRILLIANT
    assert par_labels[30] == Label.BRILLIANT
    assert seq_labels[31] == Label.FORCED
    assert par_labels[31] == Label.FORCED
    assert seq_labels[32] == Label.GREAT
    assert par_labels[32] == Label.GREAT


@require_stockfish
@require_opera
def test_parallel_is_faster_than_sequential(opera_analysis_results):
    """Đo timeit, xác nhận parallel < sequential * 0.85 (tức nhanh hơn >=15%)."""
    _, _, seq_time, par_time = opera_analysis_results
    assert par_time < seq_time * 0.85, (
        f"Chạy song song ({par_time:.2f}s) không nhanh hơn tuần tự ({seq_time:.2f}s) ít nhất 15% "
        f"(tỷ lệ: {par_time / seq_time:.2%})"
    )


@require_stockfish
def test_parallel_requires_two_pass():
    """Nếu cfg.parallel=True, cfg.two_pass=False -> fallback hoặc warning, không crash."""
    pgn_text = "1. e4 e5 *"
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    assert game is not None

    cfg = Config(two_pass=False, parallel=True, fast_depth=4, depth=6)
    pids = []
    with EnginePool(str(STOCKFISH_PATH), cfg) as pool:
        pids = [eng._e.transport.get_pid() for eng in pool.engines]
        with pytest.warns(UserWarning, match="cfg.two_pass=False"):
            reports = analyse_game_parallel(game, pool, cfg)

    assert len(reports) == 2
    for r in reports:
        assert isinstance(r, MoveReport)

    for pid in pids:
        assert not _is_pid_alive(pid)


@require_stockfish
def test_parallel_handles_no_hot_moves():
    """Ván cờ toàn nước không hot -> queue rỗng, SF2 thread nhận sentinel ngay, kết quả vẫn đúng."""
    pgn_text = "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 *"
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    assert game is not None

    cfg = Config(
        two_pass=True,
        parallel=True,
        fast_depth=4,
        depth=6,
        hot_dwc=-999.0,
        hot_gap=999.0,
        sac_min=999,
    )
    pids = []
    with EnginePool(str(STOCKFISH_PATH), cfg) as pool:
        pids = [eng._e.transport.get_pid() for eng in pool.engines]
        reports = analyse_game_parallel(game, pool, cfg)

    assert len(reports) == 6
    for r in reports:
        assert isinstance(r, MoveReport)
        assert r.verdict.label in Label

    for pid in pids:
        assert not _is_pid_alive(pid)


@require_stockfish
def test_parallel_all_hot_moves():
    """Ván cờ toàn nước hot -> SF1 và SF2 đều đào sâu đủ, không deadlock."""
    pgn_text = "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 *"
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    assert game is not None

    cfg = Config(
        two_pass=True,
        parallel=True,
        fast_depth=4,
        depth=6,
        hot_dwc=1.0,  # mọi nước đều có dwc <= 0.0 <= 1.0 nên đều hot
    )
    pids = []
    with EnginePool(str(STOCKFISH_PATH), cfg) as pool:
        pids = [eng._e.transport.get_pid() for eng in pool.engines]
        reports = analyse_game_parallel(game, pool, cfg)

    assert len(reports) == 6
    for r in reports:
        assert isinstance(r, MoveReport)
        assert r.verdict.label in Label

    for pid in pids:
        assert not _is_pid_alive(pid)
