"""Tests for EnginePool lifecycle and process cleanup (TICKET-05)."""
from __future__ import annotations

import ctypes
from pathlib import Path
import sys
import pytest

from src.core.config import Config
from src.engine.engine_pool import EnginePool
from src.engine.stockfish_client import StockfishEngine


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


STOCKFISH_PATH = find_stockfish()
require_stockfish = pytest.mark.skipif(
    STOCKFISH_PATH is None,
    reason="Stockfish binary not found at data/engines/stockfish.exe",
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
            return res != 0  # 0 là WAIT_OBJECT_0 (đã kết thúc/signaled)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    else:
        try:
            import os
            os.kill(pid, 0)
            return True
        except OSError:
            return False


@require_stockfish
def test_pool_creates_two_engines():
    """Sau __enter__, pool.engines có đúng 2 phần tử."""
    cfg = Config()
    with EnginePool(str(STOCKFISH_PATH), cfg) as pool:
        assert len(pool.engines) == 2
        assert pool.workers == 2
        for eng in pool.engines:
            assert isinstance(eng, StockfishEngine)


@require_stockfish
def test_scanner_hot_worker_accessible():
    """pool.scanner và pool.hot_worker không phải None và là StockfishEngine."""
    cfg = Config()
    with EnginePool(str(STOCKFISH_PATH), cfg) as pool:
        assert pool.scanner is not None
        assert isinstance(pool.scanner, StockfishEngine)
        assert pool.hot_worker is not None
        assert isinstance(pool.hot_worker, StockfishEngine)
        assert pool.scanner is pool.engines[0]
        assert pool.hot_worker is pool.engines[1]


@require_stockfish
def test_pool_closes_on_exit():
    """Sau with, kiểm tra không còn tiến trình stockfish.exe zombie."""
    cfg = Config()
    procs = []
    pids = []

    with EnginePool(str(STOCKFISH_PATH), cfg) as pool:
        assert len(pool.engines) == 2
        procs = [eng._e.transport._proc for eng in pool.engines]
        pids = [eng._e.transport.get_pid() for eng in pool.engines]

        for proc in procs:
            assert proc.poll() is None
        for pid in pids:
            assert _is_pid_alive(pid)

    # Sau with: pool.engines đã clear, mọi tiến trình đã thoát hoàn toàn
    assert len(pool.engines) == 0
    for proc in procs:
        assert proc.poll() is not None
    for pid in pids:
        assert not _is_pid_alive(pid)


@require_stockfish
def test_pool_closes_on_exception():
    """Raise exception trong with -> __exit__ vẫn được gọi, engine đóng sạch."""
    cfg = Config()
    procs = []
    pids = []

    with pytest.raises(RuntimeError, match="Simulation error inside with-block"):
        with EnginePool(str(STOCKFISH_PATH), cfg) as pool:
            assert len(pool.engines) == 2
            procs = [eng._e.transport._proc for eng in pool.engines]
            pids = [eng._e.transport.get_pid() for eng in pool.engines]
            raise RuntimeError("Simulation error inside with-block")

    # Sau exception: pool.engines đã clear, mọi tiến trình đã thoát hoàn toàn
    assert len(pool.engines) == 0
    for proc in procs:
        assert proc.poll() is not None
    for pid in pids:
        assert not _is_pid_alive(pid)


def test_pool_requires_minimum_two_workers():
    """EnginePool yêu cầu workers >= 2, raise ValueError nếu nhỏ hơn."""
    cfg = Config()
    with pytest.raises(ValueError, match="workers >= 2"):
        EnginePool(str(STOCKFISH_PATH or "dummy"), cfg, workers=1)
