"""Module 10 — quyết định nước nào đáng đào sâu. Hàm thuần, test bằng bảng."""
from src.core.config import Config
from src.core.schemas import MoveEval


def is_hot(ev: MoveEval, sac_value: int, cfg: Config) -> bool:
    """ev/sac_value tính từ lượt quét nhanh. Nóng = có thể là sai lầm HOẶC có thể là nước xuất sắc."""
    if ev.book or ev.forced:
        return False
    if ev.dwc <= cfg.hot_dwc:                                   # nghi mắc lỗi
        return True
    return sac_value >= cfg.sac_min or ev.mate_for_mover or ev.gap12 >= cfg.hot_gap
