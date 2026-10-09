"""Entrypoint: python main.py ván.pgn --engine <đường dẫn stockfish> [--fast] [--parallel] [--debug]"""
import argparse
from pathlib import Path
import warnings
from src.analyzer.debug import table
from src.analyzer.evaluator import Evaluator
from src.analyzer.pipeline import analyse_game
from src.core.config import Config
from src.engine.stockfish_client import StockfishEngine
from src.pgn_io.pgn_handler import annotate, read_games, write_game


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="main.py")
    ap.add_argument("pgn", help="đường dẫn file PGN đầu vào (file thật, không phải chỗ giữ chỗ)")
    ap.add_argument("--engine", required=True, help="đường dẫn stockfish")
    ap.add_argument("--depth", type=int, default=20); ap.add_argument("--multipv", type=int, default=3)
    ap.add_argument("--threads", type=int, default=4); ap.add_argument("--hash", type=int, default=512)
    ap.add_argument("--fast", action="store_true", help="quét depth 14 rồi chỉ đào sâu điểm nóng")
    ap.add_argument("--parallel", action="store_true", help="phân tích song song với 2 tiến trình Stockfish (kết hợp với --fast)")
    ap.add_argument("--debug", action="store_true", help="in bảng số liệu từng nước")
    a = ap.parse_args(argv)
    if not Path(a.pgn).is_file():
        ap.error(f"không tìm thấy file PGN: {a.pgn}")
    cfg = Config(
        depth=a.depth,
        multipv=a.multipv,
        threads=a.threads,
        hash_mb=a.hash,
        two_pass=a.fast,
        parallel=bool(a.fast and a.parallel),
    )
    out = Path(a.pgn).with_name(Path(a.pgn).stem + "_analyzed.pgn")
    out.write_text("")
    if a.parallel and not a.fast:
        warnings.warn(
            "Cảnh báo: --parallel chỉ có tác dụng khi dùng kèm --fast. "
            "Đang chạy ở chế độ tuần tự.",
            stacklevel=1,
        )

    if a.fast and a.parallel:
        from src.engine.engine_pool import EnginePool
        from src.analyzer.pipeline import analyse_game_parallel

        with EnginePool(a.engine, cfg) as pool:
            for game in read_games(a.pgn):
                reports = analyse_game_parallel(game, pool, cfg)
                if a.debug:
                    print(table(reports))
                annotate(game, reports)
                write_game(game, str(out), append=True)
    else:
        with StockfishEngine(a.engine, cfg) as eng:
            evaluator = Evaluator(eng, cfg)
            for game in read_games(a.pgn):
                reports = analyse_game(game, evaluator, cfg)
                if a.debug:
                    print(table(reports))
                annotate(game, reports)
                write_game(game, str(out), append=True)
    print("Đã ghi", out)


if __name__ == "__main__":
    main()
