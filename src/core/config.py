from dataclasses import dataclass
from src.core.enums import Label


@dataclass(frozen=True)
class Config:
    # engine
    depth: int = 20
    multipv: int = 3
    threads: int = 1
    hash_mb: int = 256
    # chạy hai lượt: quét nhanh toàn ván, chỉ đào sâu "điểm nóng"
    two_pass: bool = False
    fast_depth: int = 14
    fast_multipv: int = 2
    hot_dwc: float = -3.0      # dwc nhanh <= ngưỡng này -> nghi sai lầm, đào sâu
    hot_gap: float = 12.0      # gap12 nhanh >= ngưỡng này -> nghi nước Great/Brilliant, đào sâu
    # song song hóa (NEW)
    parallel: bool = False
    workers: int = 2
    # phân loại (đơn vị: % Win Chance, góc nhìn người đi)
    t_best: float = -2.0
    t_good: float = -5.0
    t_mistake: float = -10.0
    t_blunder: float = -20.0
    great_gap: float = 20.0
    brilliant_win_played_min: float = 60.0
    brilliant_win_best_max: float = 90.0   # bỏ qua nếu là mate-sac hoặc nước duy nhất (gap >= great_gap)
    sac_min: int = 2
    pv_plies: int = 8
    # arbitrator
    max_hits: int = 2
    min_confidence: float = 0.6


# NAG: $1 !, $2 ?, $3 !!, $4 ??, $5 !?, $6 ?!, $7 □ (chỉnh tại đây theo En Croissant của bạn)
NAG_MAP: dict[Label, int] = {
    Label.BOOK: 7, Label.BRILLIANT: 3, Label.GREAT: 1, Label.INTERESTING: 5,
    Label.INACCURACY: 6, Label.MISTAKE: 2, Label.MISS: 4, Label.BLUNDER: 4,
}
