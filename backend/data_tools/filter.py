"""图像自动筛选 - 分辨率/长宽比/文件大小/pHash 去重"""
import argparse
import logging
import shutil
from pathlib import Path
from typing import Tuple

from PIL import Image
import imagehash

from backend.configs.loader import load_paths

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

MIN_RESOLUTION = 512
MAX_FILE_MB = 10
MIN_ASPECT = 0.5
MAX_ASPECT = 2.0
PHASH_THRESHOLD = 5   # 海明距离 < 5 视为重复


def check_resolution(img_path: Path, min_size: int = MIN_RESOLUTION) -> bool:
    try:
        with Image.open(img_path) as im:
            return im.width >= min_size and im.height >= min_size
    except Exception:
        return False


def check_aspect_ratio(img_path: Path,
                       min_ratio: float = MIN_ASPECT,
                       max_ratio: float = MAX_ASPECT) -> bool:
    try:
        with Image.open(img_path) as im:
            r = im.width / im.height
            return min_ratio <= r <= max_ratio
    except Exception:
        return False


def check_file_size(img_path: Path, max_mb: float = MAX_FILE_MB) -> bool:
    return img_path.stat().st_size <= max_mb * 1024 * 1024


def compute_phash(img_path: Path) -> str:
    with Image.open(img_path) as im:
        return str(imagehash.phash(im))


def filter_image(img_path: Path) -> Tuple[bool, str]:
    """对一张图做所有检查,返回 (是否通过, 理由)"""
    if not check_resolution(img_path):
        return False, f"resolution < {MIN_RESOLUTION}"
    if not check_aspect_ratio(img_path):
        return False, f"aspect_ratio out of [{MIN_ASPECT}, {MAX_ASPECT}]"
    if not check_file_size(img_path):
        return False, f"file > {MAX_FILE_MB}MB"
    return True, "ok"


def filter_directory(in_dir: Path, out_dir: Path) -> dict:
    """筛选整个目录,通过的拷贝到 out_dir;去重基于 pHash"""
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "passed": 0, "rejected": 0, "duplicates": 0}
    seen_hashes = {}

    # 递归遍历 in_dir 中所有图片
    image_files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG", "*.webp"):
        image_files.extend(in_dir.rglob(ext))

    for img_path in image_files:
        stats["total"] += 1
        ok, reason = filter_image(img_path)
        if not ok:
            stats["rejected"] += 1
            logger.debug(f"REJECT {img_path.name}: {reason}")
            continue

        # pHash 去重
        try:
            h = compute_phash(img_path)
        except Exception as e:
            stats["rejected"] += 1
            logger.warning(f"无法计算 pHash {img_path}: {e}")
            continue

        # 检查与已通过图像的相似度
        is_dup = False
        for seen_h in seen_hashes:
            if imagehash.hex_to_hash(h) - imagehash.hex_to_hash(seen_h) < PHASH_THRESHOLD:
                is_dup = True
                break
        if is_dup:
            stats["duplicates"] += 1
            continue

        seen_hashes[h] = img_path
        # 复制到输出目录,统一命名
        out_name = f"img_{stats['passed']:04d}{img_path.suffix.lower()}"
        shutil.copy(img_path, out_dir / out_name)
        stats["passed"] += 1

    logger.info(f"筛选完成: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--in_dir", type=Path, default=None)
    parser.add_argument("--out_dir", type=Path, default=None)
    args = parser.parse_args()

    paths = load_paths()
    in_dir = args.in_dir or (paths["raw"] / args.variety)
    out_dir = args.out_dir or (paths["candidates"] / args.variety)
    filter_directory(in_dir, out_dir)


if __name__ == "__main__":
    main()
