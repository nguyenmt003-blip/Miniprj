import json
import diskcache
from src.core.schemas import Score, PVLine, PositionAnalysis

class DiskAnalysisCache:
    """Cache phân tích thế cờ trên đĩa cứng sử dụng diskcache."""

    def __init__(self, directory: str, engine_id: str) -> None:
        """
        Khởi tạo cache.
        
        :param directory: Thư mục lưu trữ cache.
        :param engine_id: ID của engine để phân biệt cache.
        """
        self.cache = diskcache.Cache(directory)
        self.engine_id = engine_id

    def _make_key(self, key: tuple[str, int, int]) -> str:
        """Tạo khóa chuỗi nội bộ từ tuple key."""
        fen_key, depth, multipv = key
        return f"{self.engine_id}:{fen_key}:{depth}:{multipv}"

    def __contains__(self, key: tuple[str, int, int]) -> bool:
        """Kiểm tra xem key có trong cache hay không."""
        return self._make_key(key) in self.cache

    def __getitem__(self, key: tuple[str, int, int]) -> PositionAnalysis:
        """Lấy phân tích từ cache."""
        k = self._make_key(key)
        if k not in self.cache:
            raise KeyError(key)
        
        raw = self.cache[k]
        d = json.loads(raw)
        
        lines = []
        for ld in d.get("lines", []):
            score = Score(cp=ld["score"].get("cp"), mate=ld["score"].get("mate"))
            lines.append(PVLine(moves=ld["moves"], score=score, rank=ld["rank"]))
            
        kwargs = {"fen": d["fen"], "lines": lines}
        if "terminal" in d:
            kwargs["terminal"] = d["terminal"]
            
        return PositionAnalysis(**kwargs)

    def __setitem__(self, key: tuple[str, int, int], pa: PositionAnalysis) -> None:
        """Lưu phân tích vào cache dưới dạng JSON string."""
        k = self._make_key(key)
        
        lines_dict = []
        for line in pa.lines:
            lines_dict.append({
                "moves": [m.uci() if hasattr(m, "uci") else str(m) for m in line.moves],
                "score": {"cp": line.score.cp, "mate": line.score.mate},
                "rank": line.rank
            })
            
        d = {"fen": pa.fen, "lines": lines_dict}
        if hasattr(pa, "terminal"):
            d["terminal"] = pa.terminal
            
        self.cache[k] = json.dumps(d)
        
    def close(self) -> None:
        """Đóng cache và giải phóng tài nguyên."""
        self.cache.close()

# --- Sửa src/analyzer/evaluator.py (2 dòng) ---
# def __init__(self, ..., cache: dict | None = None):
#     self.cache = cache if cache is not None else {}