"""Module 5 — hàm thuần: MoveEval (+ sac_value) -> (Label, rule). Không I/O, test bằng bảng."""
from src.core.config import Config
from src.core.enums import Label
from src.core.schemas import MoveEval


def classify(ev: MoveEval, cfg: Config = Config(), sac_value: int = 0) -> tuple[Label, str]:
    if ev.book:
        return Label.BOOK, "book"
    if ev.forced:
        return Label.FORCED, "forced"
    dwc = ev.dwc
    if dwc >= cfg.t_best:                                            # Nhóm A
        only_move = ev.gap12 >= cfg.great_gap
        not_already_won = ev.w_best <= cfg.brilliant_win_best_max or ev.mate_for_mover or only_move
        if sac_value >= cfg.sac_min and ev.w_played >= cfg.brilliant_win_played_min and not_already_won:
            return Label.BRILLIANT, "A.sac"
        if ev.rank == 1 and only_move:
            return Label.GREAT, "A.only_move"
        return (Label.BEST, "A.rank1") if ev.rank == 1 else (Label.EXCELLENT, "A.other")
    if dwc >= cfg.t_good:                                            # Nhóm B
        return Label.GOOD, "B"
    if dwc < cfg.t_blunder:                                          # Nhóm C
        return Label.BLUNDER, "C.blunder"
    if dwc < cfg.t_mistake:
        return Label.MISTAKE, "C.mistake"
    return Label.INACCURACY, "C.inaccuracy"
