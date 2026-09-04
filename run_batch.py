"""Batch export uses exactly the same pipeline as the web app."""
import argparse
from pathlib import Path
from core.data_loader import load_data
from core.pipeline import build_analysis
from utils.export import results_zip

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('results.zip'))
    args=parser.parse_args()
    if args.output.exists():
        parser.error('输出文件已存在，请使用新的文件名，避免覆盖已有分析。')
    bundle=build_analysis(load_data(args.input.read_bytes(),args.input.name))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(results_zip(bundle,lambda _,s:print(s)))
    print(f'完成：{args.output}；共同增长样本={int(bundle.metrics.common_growth_sample.sum())}')

if __name__=='__main__':main()
