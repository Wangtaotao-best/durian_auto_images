"""把合并后的 diffusers pipeline 转成 OpenVINO IR 格式 (CPU 推理用)"""
import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def export(model_dir: Path, output_dir: Path, dtype: str = "fp16"):
    try:
        from optimum.intel import OVStableDiffusionPipeline
    except ImportError:
        raise RuntimeError("请先 pip install optimum[openvino]")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"加载 diffusers 模型 from {model_dir} 并转 OpenVINO IR (dtype={dtype})")
    ov_pipe = OVStableDiffusionPipeline.from_pretrained(
        str(model_dir),
        export=True,
        compile=False,
    )

    logger.info(f"保存到: {output_dir}")
    ov_pipe.save_pretrained(str(output_dir))
    logger.info("OpenVINO 模型导出完成")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dtype", default="fp16", choices=["fp16", "fp32"])
    args = parser.parse_args()

    export(args.model_dir, args.output, args.dtype)


if __name__ == "__main__":
    main()
