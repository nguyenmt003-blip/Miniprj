import logging
from typing import List, Optional

from src.core.schemas import Hit
from src.detectors.base import DetectCtx, Detector, registered

logger = logging.getLogger(__name__)


def run_all(ctx: DetectCtx, detectors: Optional[List[Detector]] = None) -> List[Hit]:
    """
    Chạy danh sách các detector và gộp kết quả.
    Nếu một detector ném lỗi, ghi log và tiếp tục chạy các detector còn lại.
    """
    if detectors is None:
        detectors = registered()

    hits: List[Hit] = []
    for detector in detectors:
        try:
            results = detector.detect(ctx)
            if results:
                hits.extend(results)
        except Exception as e:
            name = getattr(detector, "name", detector.__class__.__name__)
            logger.error("Detector %s gặp lỗi: %s", name, e)

    return hits