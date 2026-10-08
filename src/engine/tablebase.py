import chess
import chess.syzygy
from typing import Optional, Any
from src.core.schemas import Score, PVLine, PositionAnalysis, fen_key

class Tablebase:
    """Quản lý Syzygy tablebases để phân tích thế cờ <= 5 quân."""

    def __init__(self, path: Optional[str], tb: Any = None) -> None:
        """
        Khởi tạo Tablebase.
        
        :param path: Đường dẫn tới thư mục chứa file Syzygy.
        :param tb: Đối tượng tablebase giả (dùng cho test).
        """
        self.tb = tb
        if self.tb is None and path is not None:
            try:
                self.tb = chess.syzygy.open_tablebase(path)
            except Exception:
                self.tb = None

    def probe(self, board: chess.Board, multipv: int = 3) -> Optional[PositionAnalysis]:
        """
        Lấy phân tích từ tablebase cho thế cờ hiện tại.
        
        :param board: Thế cờ cần phân tích.
        :param multipv: Số lượng PVLine tối đa cần trả về.
        :return: PositionAnalysis nếu thành công, ngược lại None.
        """
        if self.tb is None:
            return None
        if len(board.piece_map()) > 5:
            return None
        if board.has_castling_rights(chess.WHITE) or board.has_castling_rights(chess.BLACK):
            return None

        moves_wdl = []
        turn = board.turn
        sign = 1 if turn == chess.WHITE else -1

        for move in board.legal_moves:
            board.push(move)
            try:
                wdl_child = self.tb.probe_wdl(board)
            except KeyError:
                board.pop()
                return None
            board.pop()

            # Đảo dấu vì wdl_child là góc nhìn của bên sắp đi ở thế con
            wdl = -wdl_child
            moves_wdl.append((wdl, move))

        # Sắp xếp theo WDL giảm dần, nếu bằng nhau thì theo thứ tự UCI
        moves_wdl.sort(key=lambda x: (-x[0], x[1].uci()))

        lines = []
        for rank, (wdl, move) in enumerate(moves_wdl[:multipv], start=1):
            if wdl == 2:
                cp = 9000 * sign
            elif wdl == -2:
                cp = -9000 * sign
            else:
                cp = 0
            
            lines.append(PVLine(moves=[move], score=Score(cp=cp), rank=rank))

        if not lines:
            return None

        return PositionAnalysis(
            fen=fen_key(board),
            lines=lines
        )

    def close(self) -> None:
        """Đóng tablebase và giải phóng tài nguyên."""
        if self.tb is not None and hasattr(self.tb, "close"):
            try:
                self.tb.close()
            except Exception:
                pass

    def __enter__(self) -> "Tablebase":
        """Hỗ trợ context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Tự động đóng tablebase khi thoát khỏi block with."""
        self.close()