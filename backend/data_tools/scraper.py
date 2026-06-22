"""图像爬虫 - 从 Bing/Google 批量下载特定品种榴莲图片"""
import argparse
import logging
from pathlib import Path
from typing import List

from backend.configs.loader import load_varieties, load_paths

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def build_keywords(variety: str) -> List[str]:
    """获取品种对应的搜索关键词列表"""
    varieties = load_varieties()
    if variety not in varieties:
        raise KeyError(f"未知品种: {variety}, 可选: {list(varieties.keys())}")
    return varieties[variety]["keywords"]


def sanitize_output_dir(path: Path) -> Path:
    """确保输出目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def scrape_variety(variety: str, num_per_keyword: int = 50, out_dir: Path = None) -> int:
    """爬取一个品种的图像"""
    try:
        from icrawler.builtin import BingImageCrawler
    except ImportError:
        raise RuntimeError("请先 pip install icrawler")

    paths = load_paths()
    if out_dir is None:
        out_dir = paths["raw"] / variety
    out_dir = sanitize_output_dir(out_dir)

    keywords = build_keywords(variety)
    total_downloaded = 0

    for idx, kw in enumerate(keywords):
        logger.info(f"[{variety}] 关键词 {idx+1}/{len(keywords)}: '{kw}'")
        sub_dir = out_dir / f"kw_{idx:02d}"
        sub_dir.mkdir(exist_ok=True)
        crawler = BingImageCrawler(storage={"root_dir": str(sub_dir)})
        crawler.crawl(
            keyword=kw,
            max_num=num_per_keyword,
            min_size=(512, 512),
            file_idx_offset=0,
        )
        downloaded = len(list(sub_dir.glob("*")))
        logger.info(f"[{variety}] 关键词 '{kw}' 下载了 {downloaded} 张")
        total_downloaded += downloaded

    logger.info(f"[{variety}] 总计下载 {total_downloaded} 张到 {out_dir}")
    return total_downloaded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True, help="品种名 (musang_king/monthong/blackthorn/red_prawn)")
    parser.add_argument("--num", type=int, default=50, help="每个关键词下载数")
    parser.add_argument("--out", type=Path, default=None, help="输出目录,默认 D:/durian-data/raw/<variety>/")
    args = parser.parse_args()

    scrape_variety(args.variety, args.num, args.out)


if __name__ == "__main__":
    main()
