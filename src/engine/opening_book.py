import chess
import chess.polyglot
from typing import Optional, Any

class OpeningBook:
    """Quản lý sách khai cuộc định dạng Polyglot (.bin)."""

    def __init__(self, path: Optional[str], reader: Any = None) -> None:
        """
        Khởi tạo OpeningBook.
        
        :param path: Đường dẫn tới file .bin.
        :param reader: Reader (dùng để tiêm mock object khi test).
        """
        self._reader = reader
        if self._reader is None and path is not None:
            try:
                self._reader = chess.polyglot.open_reader(path)
            except Exception:
                self._reader = None

    def is_book(self, board: chess.Board, move: chess.Move) -> bool:
        """
        Kiểm tra xem nước đi có nằm trong sách khai cuộc tại thế cờ hiện tại không.
        
        :param board: Thế cờ hiện tại.
        :param move: Nước đi cần kiểm tra.
        :return: True nếu nước đi có trong sách, ngược lại False.
        """
        if self._reader is None:
            return False

        try:
            for entry in self._reader.find_all(board):
                if entry.move == move:
                    return True
        except Exception:
            # Xử lý trường hợp reader giả ném lỗi khi đọc
            return False

        return False

    def close(self) -> None:
        """Đóng reader và giải phóng tài nguyên."""
        if self._reader is not None and hasattr(self._reader, "close"):
            try:
                self._reader.close()
            except Exception:
                pass

    def __enter__(self) -> "OpeningBook":
        """Hỗ trợ context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Tự động đóng reader khi thoát khỏi block with."""
        self.close()