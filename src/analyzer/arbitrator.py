from collections import defaultdict
from src.core.schemas import Hit
from src.core.config import Config

def arbitrate(hits: list[Hit], parent_of: dict[str, str], cfg: Config) -> list[Hit]:
    """
    Gộp trùng, xóa hit cha khi có hit con, và lọc hit theo độ tin cậy.
    
    :param hits: Danh sách các hit đầu vào.
    :param parent_of: Từ điển ánh xạ tên hit con -> tên hit cha.
    :param cfg: Cấu hình chứa min_confidence và max_hits.
    :return: Danh sách các hit đã được lọc và gộp.
    """
    # 1. Lọc theo min_confidence
    valid = [h for h in hits if h.confidence >= cfg.min_confidence]
    
    # 2. Gộp trùng (name, perspective, squares) giữ confidence cao nhất
    best = {}
    for h in valid:
        k = (h.name, h.perspective, tuple(h.squares))
        if k not in best or h.confidence > best[k].confidence:
            best[k] = h
            
    # 3. Cùng name và squares, nếu có cả EXECUTED và MISSED thì giữ EXECUTED
    by_ns = defaultdict(list)
    for h in best.values():
        by_ns[(h.name, tuple(h.squares))].append(h)
        
    step3 = []
    for group in by_ns.values():
        persps = {h.perspective: h for h in group}
        if "EXECUTED" in persps and "MISSED" in persps:
            step3.extend(h for p, h in persps.items() if p != "MISSED")
        else:
            step3.extend(group)
            
    # 4. Xóa hit cha nếu có hit con chia sẻ ít nhất một ô
    def get_anc(name: str) -> set[str]:
        anc, curr = set(), name
        while curr in parent_of:
            curr = parent_of[curr]
            anc.add(curr)
        return anc

    to_remove = set()
    for i, h1 in enumerate(step3):
        sq1 = set(h1.squares)
        for j, h2 in enumerate(step3):
            if i != j and h1.name in get_anc(h2.name) and sq1.intersection(h2.squares):
                to_remove.add(i)
                break
                
    step4 = [h for i, h in enumerate(step3) if i not in to_remove]
    
    # 5. Mỗi perspective tối đa max_hits, sắp theo confidence giảm dần
    by_p = defaultdict(list)
    for h in step4:
        by_p[h.perspective].append(h)
        
    res = []
    for group in by_p.values():
        group.sort(key=lambda x: x.confidence, reverse=True)
        res.extend(group[:cfg.max_hits])
        
    return res