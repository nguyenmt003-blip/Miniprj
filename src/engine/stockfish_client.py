"""Cài đặt Engine bằng Stockfish (UCI). Score luôn theo góc nhìn Trắng."""
from __future__ import annotations
import chess, chess.engine
from src.core.config import Config
from src.core.schemas import PVLine, Score


class StockfishEngine:
    def __init__(self, path: str, cfg: Config = Config()):
        self.cfg = cfg
        self._e = chess.engine.SimpleEngine.popen_uci(path)
        self._e.configure({"Threads": cfg.threads, "Hash": cfg.hash_mb})

    def analyse(self, board: chess.Board, multipv: int, depth: int) -> list[PVLine]:
        infos = self._e.analyse(board, chess.engine.Limit(depth=depth), multipv=multipv)
        out = []
        for i, info in enumerate(infos, 1):
            sc = info["score"].white()
            mate = sc.mate()
            score = Score(mate=mate) if mate is not None else Score(cp=sc.score())
            out.append(PVLine(i, tuple(m.uci() for m in info.get("pv", [])), score))
        return out

    def close(self) -> None:
        self._e.quit()

    def __enter__(self): return self
    def __exit__(self, *a): self.close()
