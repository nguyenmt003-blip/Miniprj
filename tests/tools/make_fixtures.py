import csv
import yaml
import chess
import argparse
from typing import Iterable

def build(rows: Iterable[dict], theme: str, n: int) -> list[dict]:
    """
    Lọc và tạo fixture từ dữ liệu Lichess puzzle.
    
    :param rows: Iterable chứa các dòng dữ liệu (dict).
    :param theme: Theme cần lọc.
    :param n: Số lượng kết quả tối đa.
    :return: Danh sách các fixture dương tính.
    """
    results = []
    for row in rows:
        if len(results) >= n:
            break
            
        themes = row.get("Themes", "")
        if theme not in themes.split():
            continue
            
        try:
            rd = int(row.get("RatingDeviation", 1000))
            pop = int(row.get("Popularity", 0))
        except ValueError:
            continue
            
        if rd >= 100 or pop <= 90:
            continue
            
        moves = row.get("Moves", "").split()
        if len(moves) < 2:
            continue
            
        try:
            board = chess.Board(row["FEN"])
            board.push(chess.Move.from_uci(moves[0]))
        except ValueError:
            continue
            
        results.append({
            "fen": board.fen(),
            "move": moves[1],
            "puzzle_id": row.get("PuzzleId", ""),
            "themes": themes
        })
        
    return results

def main() -> None:
    """Điểm vào CLI."""
    parser = argparse.ArgumentParser(description="Tạo fixture từ Lichess puzzles CSV.")
    parser.add_argument("--csv", required=True, help="Đường dẫn file CSV.")
    parser.add_argument("--theme", required=True, help="Theme cần lọc.")
    parser.add_argument("--n", type=int, default=10, help="Số lượng kết quả tối đa.")
    parser.add_argument("--out", required=True, help="Đường dẫn file YAML đầu ra.")
    args = parser.parse_args()
    
    with open(args.csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fixtures = build(reader, args.theme, args.n)
        
    output_data = {
        "positive": fixtures,
        "negative": []  # Âm tính bắt buộc duyệt tay
    }
    
    with open(args.out, "w", encoding="utf-8") as f:
        yaml.dump(output_data, f, sort_keys=False, allow_unicode=True)

if __name__ == "__main__":
    main()