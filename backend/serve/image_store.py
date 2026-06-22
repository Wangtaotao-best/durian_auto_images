"""把生成的 PIL 图像保存到磁盘,提供 URL 访问"""
import io
from pathlib import Path
from typing import List
from PIL import Image


class ImageStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, task_id: str, images: List[Image.Image]) -> List[str]:
        task_dir = self.root / task_id
        task_dir.mkdir(exist_ok=True)
        urls = []
        for i, img in enumerate(images):
            path = task_dir / f"{i}.png"
            img.save(path, "PNG")
            urls.append(f"/api/tasks/{task_id}/image?idx={i}")
        return urls

    def load_bytes(self, task_id: str, idx: int) -> bytes:
        path = self.root / task_id / f"{idx}.png"
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_bytes()
