chess_analyzer/
├── pytest.ini                  # [Phase 1] Cấu hình pythonpath = . để import từ gốc
├── main.py                     # [Phase 1] Entrypoint
├── config/
│   └── tactics_registry.yaml   # [Phase 2] Single Source of Truth cho 56 chiến thuật
├── templates/                  
│   └── vi.yaml                 # [Phase 2] Phase 1 sẽ dùng dict hardcode trong text_generator.py
├── data/                       # [Phase 2]
│   ├── books/                  
│   └── syzygy/                 
├── cache/                      # [Phase 2] Disk cache
│
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # [Phase 1] Hardcode dataclass trước, load YAML sau
│   │   ├── enums.py            # [Phase 1] (Từ contracts.py)
│   │   ├── schemas.py          # [Phase 1] (Từ contracts.py) Đã làm mỏng
│   │   ├── winchance.py        # [Phase 1] Toán thuần túy, không phụ thuộc
│   │   └── registry.py         # [Phase 2] Đọc tactics_registry.yaml
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── protocol.py         # [Phase 1] Giao diện (Protocol/ABC) cho Engine
│   │   ├── stockfish_client.py # [Phase 1] Implement Protocol gọi UCI
│   │   ├── analysis_cache.py   # [Phase 2]
│   │   ├── opening_book.py     # [Phase 2]
│   │   └── tablebase.py        # [Phase 2]
│   │
│   ├── primitives/
│   │   ├── __init__.py
│   │   ├── material.py         # [Phase 1] Đếm vật chất
│   │   ├── pv_tools.py         # [Phase 1] Duyệt PV line
│   │   └── see.py              # [Phase 2] Đệ quy đơn giản
│   │
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── positional.py       # [Phase 2] Chưa cần ở Phase 1
│   │
│   ├── detectors/              # [Phase 2] Toàn bộ thư mục này làm sau
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dispatcher.py
│   │   ├── static/
│   │   ├── transition/
│   │   └── search_pv/
│   │
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── evaluator.py        # [Phase 1] Gọi engine để lấy điểm
│   │   ├── scheduler.py        # [Phase 2] Điều phối việc gọi engine (depth, multipv)
│   │   ├── classifier.py       # [Phase 1] Phân loại nước đi (Brilliant, Blunder...)
│   │   ├── text_generator.py   # [Phase 1] (Từ commentary.py) Dùng dict nội bộ trước
│   │   ├── pipeline.py         # [Phase 1] Nối Core -> Engine -> Analyzer
│   │   ├── arbitrator.py       # [Phase 2] Lọc chiến thuật (chưa có detector nên chưa cần)
│   │   └── debug.py
│   │
│   └── pgn_io/
│       ├── __init__.py
│       ├── pgn_handler.py      # [Phase 1] Đọc/Ghi PGN, sanitize comment
│       └── watcher.py          # [Phase 2] Watchdog tự động
│
└── tests/
    ├── __init__.py
    ├── pytest.ini              # (Tùy chọn, thường dùng chung file ở root)
    ├── architecture/
    │   ├── __init__.py
    │   └── test_dependencies.py# [Phase 1] Quét import, ép chiều phụ thuộc
    ├── mocks/
    │   ├── __init__.py
    │   └── scripted_engine.py  # [Phase 1] Engine giả (Mock) trả về eval định sẵn để test
    ├── fixtures/
    │   ├──  pins_lichess.yaml   # [Phase 2] Data test từ Lichess
    │   └── opera_game.pgn
    ├── core/                   # Phản chiếu src/core/
    │   ├── __init__.py
    │   └── test_winchance.py   # [Phase 1] Test công thức toán
    ├── engine/                 # Phản chiếu src/engine/
    │   ├── __init__.py
    │   └── test_stockfish.py   # [Phase 1]
    ├── analyzer/               # Phản chiếu src/analyzer/
    │   ├── __init__.py
    │   ├── test_classifier.py  # [Phase 1]
    │   └── test_pipeline.py    # [Phase 1] Test lát cắt dọc (Opera Game)
    └── detectors/              # Phản chiếu src/detectors/
        ├── __init__.py
        └── test_pins.py        # [Phase 2] Test dựa trên fixtures
        