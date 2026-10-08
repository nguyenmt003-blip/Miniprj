import chess
from src.primitives.material import VALUES

def see(board: chess.Board, move: chess.Move) -> int:
    """
    Đánh giá trao đổi tĩnh (SEE) của một nước ăn quân.
    
    :param board: Thế cờ hiện tại.
    :param move: Nước đi cần đánh giá.
    :return: Giá trị SEE theo góc nhìn bên thực hiện nước đi.
    """
    if not board.is_capture(move):
        return 0

    target = move.to_square
    
    if board.is_en_passant(move):
        captured_val = VALUES[chess.PAWN]
        ep_square = chess.square(chess.file_index(target), chess.rank_index(move.from_square))
    else:
        captured = board.piece_at(target)
        captured_val = VALUES[captured.piece_type] if captured else 0
        ep_square = None

    moving = board.piece_at(move.from_square)
    if not moving:
        return 0
        
    current_piece_val = VALUES[move.promotion] if move.promotion else VALUES[moving.piece_type]
    
    b = board.copy()
    b.remove_piece_at(move.from_square)
    if ep_square is not None:
        b.remove_piece_at(ep_square)
        
    gains = [captured_val]
    turn = not board.turn
    
    while True:
        attackers = b.attackers(turn, target)
        if not attackers:
            break
            
        min_val = float('inf')
        min_sq = None
        for sq in attackers:
            p = b.piece_at(sq)
            if p:
                val = VALUES[p.piece_type]
                if val < min_val:
                    min_val = val
                    min_sq = sq
                    
        if min_sq is None:
            break
            
        gains.append(current_piece_val)
        
        p = b.piece_at(min_sq)
        current_piece_val = VALUES[p.piece_type] if p else 0
        
        b.remove_piece_at(min_sq)
        turn = not turn
        
    res = 0
    for i in range(len(gains) - 1, 0, -1):
        res = max(0, gains[i] - res)
        
    return gains[0] - res