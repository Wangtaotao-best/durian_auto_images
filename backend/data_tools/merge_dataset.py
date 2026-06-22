"""合并爬虫候选 + 个人数据集 → 训练数据"""
import argparse
import logging
import shutil
from pathlib import Path

from PIL import Image
import imagehash

from backend.configs.loader import load_paths

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

PHASH_THRESHOLD = 5


def resize_image(src: Path, dst: Path, target_short: int = 512) -> Path:
    """按短边等比缩放到 target_short"""
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        if min(w, h) > target_short:
            scale = target_short / min(w, h)
            new_size = (int(w * scale), int(h * scale))
            im = im.resize(new_size, Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "JPEG", quality=92)
    return dst


def merge_sources(variety: str, crawl_dir: Path, personal_dir: Path,
                  out_dir: Path, target_short: int = 512) -> dict:
    """合并两个源到 out_dir,自动 resize + pHash 去重"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "added": 0, "duplicates": 0, "from_crawl": 0, "from_personal": 0}
    seen = {}
    idx = 0

    def _process(src_dir: Path, tag: str):
        nonlocal idx
        if not src_dir or not Path(src_dir).exists():
            return
        for src in sorted(Path(src_dir).rglob("*")):
            if src.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            stats["total"] += 1
            try:
                h = str(imagehash.phash(Image.open(src)))
            except Exception:
                continue
            is_dup = any(
                imagehash.hex_to_hash(h) - imagehash.hex_to_hash(sh) < PHASH_THRESHOLD
                for sh in seen
            )
            if is_dup:
                stats["duplicates"] += 1
                continue
            seen[h] = True
            dst = out_dir / f"{variety}_{tag}_{idx:04d}.jpg"
            try:
                resize_image(src, dst, target_short)
                idx += 1
                stats["added"] += 1
                stats[f"from_{tag}"] += 1
            except Exception as e:
                logger.warning(f"处理失败 {src}: {e}")

    _process(crawl_dir, "crawl")
    _process(personal_dir, "personal")
    logger.info(f"合并完成 {variety}: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--crawl_dir", type=Path, default=None)
    parser.add_argument("--personal_dir", type=Path, default=None)
    parser.add_argument("--out_dir", type=Path, default=None)
    args = parser.parse_args()

    paths = load_paths()
    crawl_dir = args.crawl_dir or (paths["candidates"] / args.variety)
    personal_dir = args.personal_dir or (paths["personal"] / args.variety)
    out_dir = args.out_dir or (paths["training"] / args.variety)
    merge_sources(args.variety, crawl_dir, personal_dir, out_dir)


if __name__ == "__main__":
    main()
