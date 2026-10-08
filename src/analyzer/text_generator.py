import os
import yaml
from src.core.enums import Label
from src.core.schemas import MoveEval, Verdict


class SafeDict(dict):
    """Dictionary an toàn cho format_map, giữ nguyên placeholder nếu thiếu key."""
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class TextGenerator:
    """Sinh bình luận từ template YAML."""
    
    def __init__(self, templates_dir: str = "templates") -> None:
        """Khởi tạo TextGenerator với thư mục chứa template."""
        self.templates_dir = templates_dir

    def _load(self, lang: str) -> dict:
        """Tải nội dung file YAML theo ngôn ngữ."""
        path = os.path.join(self.templates_dir, f"{lang}.yaml")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def render(self, ev: MoveEval, v: Verdict, lang: str = "vi") -> str:
        """Sinh chuỗi bình luận cho nước đi dựa trên nhãn và chiến thuật."""
        label_name = v.label.name if v.label else "NONE"
        
        data = self._load(lang)
        template = data.get("labels", {}).get(label_name)
        
        if not template:
            en_data = self._load("en")
            template = en_data.get("labels", {}).get(label_name, label_name)
            
        san = getattr(ev, "move_san", "")
        best = getattr(ev, "best_san", "")
            
        try:
            text = template.format_map(SafeDict(san=san, best=best))
        except Exception:
            text = template
            
        if getattr(v, "hits", None):
            hit_names = ", ".join(h.name for h in v.hits)
            text += f" Chiến thuật: {hit_names}."
            
        return text


def make_comment(ev: MoveEval, v: Verdict, lang: str = "vi") -> str:
    """Điểm vào cho pipeline sinh bình luận."""
    generator = TextGenerator()
    return generator.render(ev, v, lang)