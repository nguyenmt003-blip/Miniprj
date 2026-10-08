import os
import time
import queue
import logging
import threading
from pathlib import Path
from typing import Callable, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

def is_candidate(path: str) -> bool:
    """
    Kiểm tra xem file có phải là PGN cần xử lý không.
    
    :param path: Đường dẫn file.
    :return: True nếu là file .pgn và không kết thúc bằng _analyzed.pgn.
    """
    p = str(path).lower()
    return p.endswith('.pgn') and not p.endswith('_analyzed.pgn')

def wait_until_stable(
    path: str, 
    checks: int = 2, 
    interval: float = 0.5, 
    size_fn: Callable[[str], int] = os.path.getsize, 
    sleep: Callable[[float], None] = time.sleep
) -> bool:
    """
    Đợi đến khi kích thước file ổn định (không thay đổi sau `checks` lần kiểm tra).
    
    :param path: Đường dẫn file.
    :param checks: Số lần kiểm tra kích thước không đổi liên tiếp.
    :param interval: Thời gian chờ giữa các lần kiểm tra.
    :param size_fn: Hàm lấy kích thước file (dùng để test).
    :param sleep: Hàm sleep (dùng để test).
    :return: True nếu file ổn định, False nếu file không tồn tại.
    """
    try:
        prev_size = -1
        stable_count = 0
        while stable_count < checks:
            current_size = size_fn(path)
            if current_size == prev_size:
                stable_count += 1
            else:
                stable_count = 0
                prev_size = current_size
            
            if stable_count < checks:
                sleep(interval)
        return True
    except FileNotFoundError:
        return False

class _PgnHandler(FileSystemEventHandler):
    """Handler nội bộ để đẩy sự kiện file mới vào hàng đợi."""
    def __init__(self, q: queue.Queue) -> None:
        self.q = q

    def on_created(self, event: Any) -> None:
        if not event.is_directory and is_candidate(event.src_path):
            self.q.put(Path(event.src_path))

    def on_moved(self, event: Any) -> None:
        if not event.is_directory and is_candidate(event.dest_path):
            self.q.put(Path(event.dest_path))

class PgnWatcher:
    """Theo dõi thư mục để phát hiện và xử lý file PGN mới bằng luồng riêng."""

    def __init__(self, input_dir: str | Path, on_new: Callable[[Path], None]) -> None:
        """
        Khởi tạo PgnWatcher.
        
        :param input_dir: Thư mục cần theo dõi.
        :param on_new: Callback được gọi khi có file mới và đã ổn định.
        """
        self.input_dir = Path(input_dir)
        self.on_new = on_new
        self.q: queue.Queue = queue.Queue()
        self.observer = Observer()
        self.observer.schedule(_PgnHandler(self.q), str(self.input_dir), recursive=False)
        self._stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)

    def _worker(self) -> None:
        """Luồng worker lấy file từ hàng đợi, đợi ổn định và gọi callback."""
        while not self._stop_event.is_set():
            try:
                path = self.q.get(timeout=0.1)
            except queue.Empty:
                continue
            
            if wait_until_stable(str(path)):
                try:
                    self.on_new(path)
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý {path}: {e}")
            self.q.task_done()

    def start(self) -> None:
        """Bắt đầu theo dõi thư mục và chạy luồng worker."""
        self._stop_event.clear()
        self.worker_thread.start()
        self.observer.start()

    def stop(self) -> None:
        """Dừng theo dõi và luồng worker."""
        self._stop_event.set()
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        if self.worker_thread.is_alive():
            self.worker_thread.join()