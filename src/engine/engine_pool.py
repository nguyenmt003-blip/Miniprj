"""Quản lý pool nhiều tiến trình Stockfish để phân tích song song."""
from __future__ import annotations

from src.core.config import Config
from src.engine.stockfish_client import StockfishEngine


class EnginePool:
    """Quản lý vòng đời của nhiều tiến trình Stockfish chạy song song.

    Sử dụng dưới dạng context manager để đảm bảo mọi subprocess đều được
    dọn sạch ngay cả khi có ngoại lệ xảy ra giữa chừng.

    Attributes:
        scanner:    Engine #1 — quét nhanh toàn ván rồi work-steal deep scan.
        hot_worker: Engine #2 — dedicated deep worker chạy song song Phase 1.

    Example::

        with EnginePool("stockfish.exe", cfg) as pool:
            pool.scanner.analyse(board, ...)
            pool.hot_worker.analyse(board, ...)
        # Sau with: cả 2 stockfish.exe đã quit() sạch
    """

    def __init__(self, engine_path: str, cfg: Config, workers: int = 2) -> None:
        """Khởi tạo pool (chưa mở tiến trình — chờ đến __enter__).

        Args:
            engine_path: Đường dẫn tới file thực thi Stockfish.
            cfg:         Cấu hình dùng chung cho tất cả engine trong pool.
            workers:     Số lượng engine; phải >= 2.

        Raises:
            ValueError: Nếu workers < 2.
        """
        if workers < 2:
            raise ValueError(f"EnginePool yêu cầu workers >= 2, nhận được {workers}.")
        self.engine_path = engine_path
        self.cfg = cfg
        self.workers = workers
        self.engines: list[StockfishEngine] = []

    # ------------------------------------------------------------------ #
    # Context manager                                                      #
    # ------------------------------------------------------------------ #

    def __enter__(self) -> EnginePool:
        """Mở tất cả tiến trình Stockfish."""
        self.engines = [
            StockfishEngine(self.engine_path, self.cfg)
            for _ in range(self.workers)
        ]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Đóng tất cả tiến trình — kể cả khi có ngoại lệ."""
        self.close()

    # ------------------------------------------------------------------ #
    # Named properties (tránh truy cập bằng index dễ nhầm)               #
    # ------------------------------------------------------------------ #

    @property
    def scanner(self) -> StockfishEngine:
        """Engine #1: fast scan toàn ván, sau đó work-steal deep scan."""
        return self.engines[0]

    @property
    def hot_worker(self) -> StockfishEngine:
        """Engine #2: dedicated deep worker chạy song song với Phase 1."""
        return self.engines[1]

    # ------------------------------------------------------------------ #
    # Cleanup                                                              #
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """Đóng từng engine độc lập; lỗi 1 engine không chặn đóng cái còn lại."""
        for eng in self.engines:
            try:
                eng.close()
            except Exception:
                pass
        self.engines.clear()
