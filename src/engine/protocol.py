"""Giao diện engine: phần còn lại của dự án chỉ biết Engine.analyse()."""
from typing import Protocol
import chess
from src.core.schemas import PVLine


class Engine(Protocol):
    def analyse(self, board: chess.Board, multipv: int, depth: int) -> list[PVLine]: ...
