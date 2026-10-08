import chess
from src.core.schemas import Hit
from src.detectors.base import DetectCtx, register
from src.primitives.material import VALUES

def _get_pins(board: chess.Board, color: chess.Color) -> set[tuple[str, chess.Square, chess.Square, chess.Square]]:
    """Tìm tất cả các ghim (tuyệt đối và tương đối) do phe `color` tạo ra."""
    opp_color = not color
    pins = set()
    
    pinners = board.pieces(chess.BISHOP, color) | board.pieces(chess.ROOK, color) | board.pieces(chess.QUEEN, color)
    for pinner_sq in pinners:
        attacks = board.attacks(pinner_sq)
        for pinned_sq in attacks & board.occupied_co[opp_color]:
            pinned_piece = board.piece_at(pinned_sq)
            # Vua không thể là quân bị ghim
            if not pinned_piece or pinned_piece.piece_type == chess.KING:
                continue
                
            # Thử bỏ quân bị ghim để xem tia tấn công tiếp theo
            board.remove_piece_at(pinned_sq)
            new_attacks = board.attacks(pinner_sq) & ~attacks
            board.set_piece_at(pinned_sq, pinned_piece)
            
            behind_sqs = new_attacks & board.occupied_co[opp_color]
            for behind_sq in behind_sqs:
                behind_piece = board.piece_at(behind_sq)
                if not behind_piece:
                    continue
                    
                if behind_piece.piece_type == chess.KING:
                    pins.add(("Absolute Pin", pinned_sq, pinner_sq, behind_sq))
                else:
                    # Ghim tương đối: quân phía sau có giá trị lớn hơn quân bị ghim
                    if VALUES[behind_piece.piece_type] > VALUES[pinned_piece.piece_type]:
                        pins.add(("Relative Pin", pinned_sq, pinner_sq, behind_sq))
                        
    return pins

@register
class Pins:
    """Detector phát hiện ghim tuyệt đối và ghim tương đối."""
    
    name = "Pins"
    
    def detect(self, ctx: DetectCtx) -> list[Hit]:
        """
        Phát hiện ghim sau nước đi.
        
        :param ctx: Context chứa thế cờ trước nước đi và nước đi.
        :return: Danh sách các Hit chứa thông tin ghim.
        """
        turn = ctx.board.turn
        
        b_after = ctx.board.copy()
        b_after.push(ctx.move)
        
        pins_before = _get_pins(ctx.board, turn)
        pins_after = _get_pins(b_after, turn)
        
        hits = []
        for pin in pins_after:
            pin_type, pinned_sq, pinner_sq, behind_sq = pin
            
            # Chỉ báo nếu ghim chưa tồn tại ở thế trước, hoặc quân vừa đi chính là quân ghim
            if pin not in pins_before or pinner_sq == ctx.move.to_square:
                hits.append(Hit(
                    name=pin_type,
                    squares=(pinned_sq, pinner_sq, behind_sq)
                ))
                
        return hits