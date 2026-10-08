"""Bảng debug: nhìn một phát là biết lỗi nằm ở eval hay ở luật."""
from src.core.schemas import MoveReport


def table(reports: list[MoveReport]) -> str:
    rows = [f"{'ply':>3} {'san':<8} {'rk':>2} {'Wbest':>6} {'Wplay':>6} {'W2':>6} {'dwc':>6} {'sac':>3}  label/rule"]
    for r in reports:
        e, v = r.eval, r.verdict
        w2 = "-" if e.w_second is None else f"{e.w_second:.1f}"
        rows.append(f"{e.ply:>3} {e.move_san:<8} {e.rank:>2} {e.w_best:>6.1f} {e.w_played:>6.1f} "
                    f"{w2:>6} {v.dwc:>6.1f} {v.sac_value:>3}  {v.label.value}/{v.rule}")
    return "\n".join(rows)
