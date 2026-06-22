"""BLIP 自动给训练图打英文 caption,并拼接品种触发词"""
import argparse
import csv
import logging
from pathlib import Path

from backend.configs.loader import load_varieties, load_paths

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def build_full_caption(trigger: str, blip_text: str) -> str:
    """拼接最终 caption: <触发词>, <BLIP 文本>, high quality, detailed"""
    blip_text = blip_text.strip().rstrip(".")
    return f"{trigger}, {blip_text}, high quality, detailed"


def caption_directory(variety: str, dir_path: Path,
                      model_id: str = "Salesforce/blip-image-captioning-large") -> int:
    """对目录中所有图打 caption,生成同名 .txt 文件 + 汇总 captions.csv"""
    try:
        import torch
        from PIL import Image
        from transformers import BlipProcessor, BlipForConditionalGeneration
    except ImportError as e:
        raise RuntimeError(f"缺少依赖: {e}")

    varieties = load_varieties()
    trigger = varieties[variety]["trigger"]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info(f"加载 BLIP 模型 {model_id} 到 {device}")
    processor = BlipProcessor.from_pretrained(model_id)
    model = BlipForConditionalGeneration.from_pretrained(model_id).to(device)
    model.eval()

    dir_path = Path(dir_path)
    image_files = sorted(
        [p for p in dir_path.iterdir()
         if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    )

    captions_csv = dir_path / "captions.csv"
    count = 0
    with open(captions_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "blip_text", "final_caption"])
        for img_path in image_files:
            try:
                image = Image.open(img_path).convert("RGB")
                inputs = processor(image, return_tensors="pt").to(device)
                with torch.no_grad():
                    out = model.generate(**inputs, max_length=50, num_beams=4)
                blip_text = processor.decode(out[0], skip_special_tokens=True)
                final = build_full_caption(trigger, blip_text)
                # 写同名 .txt
                txt_path = img_path.with_suffix(".txt")
                txt_path.write_text(final, encoding="utf-8")
                writer.writerow([img_path.name, blip_text, final])
                count += 1
                if count % 10 == 0:
                    logger.info(f"已处理 {count}/{len(image_files)}")
            except Exception as e:
                logger.warning(f"caption 失败 {img_path}: {e}")

    logger.info(f"完成: {count} 张图打标,汇总写入 {captions_csv}")
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--dir", type=Path, default=None)
    args = parser.parse_args()

    paths = load_paths()
    dir_path = args.dir or (paths["training"] / args.variety)
    caption_directory(args.variety, dir_path)


if __name__ == "__main__":
    main()
