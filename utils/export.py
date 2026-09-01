"""In-memory exports; no uploaded files or session results share a disk folder."""
from io import BytesIO
import json
from datetime import datetime, timezone
import zipfile
import pandas as pd
from core.config import DPI
from core.catalog import CHARTS, TABLES
from core.view_data import chart_data
from plots.registry import render_chart, ChartUnavailable, PLOT_LOCK
from .excel_format import _format_workbook

def safe_frame(frame):
    # Protect spreadsheet viewers from formula injection in user-supplied text.
    result=frame.copy()
    for col in result.select_dtypes(include=['object','string']).columns:
        result[col]=result[col].map(lambda x: "'"+x if isinstance(x,str) and x.lstrip().startswith(('=','+','-','@')) else x)
    return result

def csv_bytes(frame):
    return safe_frame(frame).to_csv(index=False).encode('utf-8-sig')

def xlsx_bytes(sheets):
    output=BytesIO()
    with pd.ExcelWriter(output,engine='openpyxl') as writer:
        for name,frame in sheets.items():
            safe_frame(frame).to_excel(writer,sheet_name=name[:31],index=False)
        _format_workbook(writer)
    return output.getvalue()

def figure_bytes(fig,fmt='png'):
    output=BytesIO()
    with PLOT_LOCK:
        fig.savefig(output,format=fmt,dpi=DPI,bbox_inches='tight',facecolor='white')
    return output.getvalue()

def results_zip(bundle, progress=None):
    output=BytesIO()
    skipped=[]
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for i,(code,meta) in enumerate(CHARTS.items()):
            if progress: progress(i/len(CHARTS),f'检查并生成 {code} · {meta[0]}')
            try:
                fig=render_chart(bundle,code)
            except ChartUnavailable as exc:
                skipped.append(f'{code}: {exc}')
                if progress: progress(i/len(CHARTS),f'跳过 {code} · 当前数据不满足条件')
                continue
            folder='core' if code.startswith('F') else 'additional'
            archive.writestr(f'figures/{folder}/{meta[1]}.png',figure_bytes(fig))
            archive.writestr(f'figures/vector/{meta[1]}.pdf',figure_bytes(fig,'pdf'))
            archive.writestr(f'figure_data/{code}_data.csv',csv_bytes(chart_data(bundle,code)))
        for code,sheets in bundle.tables.items():
            archive.writestr(f'tables/{TABLES[code][1]}.xlsx',xlsx_bytes(sheets))
            for sheet,frame in sheets.items():
                archive.writestr(f'tables/{code}_{sheet}.csv',csv_bytes(frame))
        for name,frame in bundle.processed().items():
            archive.writestr('processed_data/'+name,csv_bytes(frame))
        archive.writestr('validation_report.txt',bundle.loaded.report+'\n'+'\n'.join(bundle.warnings))
        manifest={'source_filename':bundle.loaded.filename,'source_sha256':bundle.loaded.digest,
                  'created_utc':datetime.now(timezone.utc).isoformat(), 'config':bundle.config.to_dict(),
                  'missing_or_unavailable':skipped,'data_rows':len(bundle.metrics),
                  'common_growth_n':int(bundle.metrics.common_growth_sample.sum()),
                  'note':'缺失年份不插值。F02/F03使用当前显示区间；其他图遵从各自样本期。'}
        archive.writestr('analysis_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        archive.writestr('README.txt','图与对应数据共用本次计算结果。未满足样本条件的图见analysis_manifest.json。\n'
                          '图A01沿用原版横轴%刻度，实际增长差单位为百分点（pp）。\n'
                          '原始文件不包含在导出包中；来源文件名、SHA256、配置均已记录。\n')
    if progress: progress(1.0,'全部可用结果已准备完成')
    return output.getvalue()
