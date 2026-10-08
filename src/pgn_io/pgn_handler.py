"""Module 8 — đọc/ghi PGN. Không biết gì về engine hay phân loại."""
from __future__ import annotations
from typing import Iterator
import chess.pgn
from src.core.schemas import MoveReport


def read_games(path: str) -> Iterator[chess.pgn.Game]:
    with open(path, encoding="utf-8") as f:
        while (game := chess.pgn.read_game(f)) is not None:
            yield game


def annotate(game: chess.pgn.Game, reports: list[MoveReport]) -> None:
    for node, rep in zip(game.mainline(), reports):
        v = rep.verdict
        node.nags = {v.nag} if v.nag else set()
        node.comment = v.commentary.replace("}", "")      # '}' làm hỏng cú pháp PGN


def write_game(game: chess.pgn.Game, path: str, append: bool = False) -> None:
    with open(path, "a" if append else "w", encoding="utf-8") as f:
        game.accept(chess.pgn.FileExporter(f))
        f.write("\n")
