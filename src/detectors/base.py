import chess
from dataclasses import dataclass
from typing import Protocol, List, Type

from src.core.schemas import Hit, MoveEval
from src.core.config import Config


@dataclass
class DetectCtx:
    """Ngữ cảnh truyền cho các detector, board là thế cờ trước nước đi."""
    board: chess.Board
    move: chess.Move
    ev: MoveEval
    cfg: Config


class Detector(Protocol):
    """Giao diện chung cho mọi detector."""
    name: str

    def detect(self, ctx: DetectCtx) -> List[Hit]:
        """Phát hiện và trả về danh sách các Hit."""
        ...


_registry: List[Detector] = []


def register(cls: Type[Detector]) -> Type[Detector]:
    """Decorator để khởi tạo và đăng ký một detector vào hệ thống."""
    _registry.append(cls())
    return cls


def registered() -> List[Detector]:
    """Trả về danh sách các detector đã được đăng ký."""
    return _registry.copy()