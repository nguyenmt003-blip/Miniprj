import chess
from src.core.schemas import Hit
from src.detectors.base import DetectCtx, register
from src.primitives.material import VALUES
from src.primitives.see import see

@register
class Fork:
    """Detector phát hiện đòn đôi (Fork) sau một nước đi."""
    
    name = "Fork"
    
    def detect(self, ctx: DetectCtx) -> list[Hit]:
        """
        Phát hiện đòn đôi.
        
        :param ctx: Context chứa thế cờ trước nước đi và nước đi.
        :return: Danh sách các Hit chứa thông tin đòn đôi.
        """
        # Nếu là nước ăn quân, kiểm tra xem có bị lỗ không bằng SEE
        if ctx.board.is_capture(ctx.move):
            if see(ctx.board, ctx.move) < 0:
                return []
                
        b = ctx.board.copy()
        b.push(ctx.move)
        
        sq = ctx.move.to_square
        piece = b.piece_at(sq)
        if not piece:
            return []
            
        piece_val = VALUES[piece.piece_type]
        opp_color = b.turn  # Lượt tiếp theo là của đối thủ
        
        # Nếu không phải nước ăn quân, kiểm tra xem ô đến có bị quân rẻ hơn tấn công không
        if not ctx.board.is_capture(ctx.move):
            attackers = b.attackers(opp_color, sq)
            for atk_sq in attackers:
                atk_piece = b.piece_at(atk_sq)
                if atk_piece and VALUES[atk_piece.piece_type] < piece_val:
                    return []
                    
        attacks = b.attacks(sq)
        valid_targets = []
        
        for target_sq in attacks & b.occupied_co[opp_color]:
            target_piece = b.piece_at(target_sq)
            if not target_piece:
                continue
                
            target_val = VALUES[target_piece.piece_type]
            
            # Điều kiện mục tiêu hợp lệ:
            # 1. Là Vua
            # 2. Hoặc có giá trị >= giá trị quân đi
            # 3. Hoặc không được bảo vệ
            is_king = target_piece.piece_type == chess.KING
            is_valuable = target_val >= piece_val
            is_unprotected = not b.is_attacked_by(opp_color, target_sq)
            
            if is_king or is_valuable or is_unprotected:
                valid_targets.append(target_sq)
                
        if len(valid_targets) >= 2:
            valid_targets.sort()
            return [Hit(name=self.name, squares=(sq, *valid_targets))]
            
        return []