"""In-memory Excel ingestion; no global paths and no writes of uploaded workbooks."""
from dataclasses import dataclass
from io import BytesIO
import hashlib
import zipfile
import pandas as pd
from .config import *
from .validation import _clean_and_validate_sheet

class DataInputError(ValueError):
    def __init__(self, messages, report=''):
        self.messages = [messages] if isinstance(messages, str) else list(messages)
        self.report = report or '\n'.join(self.messages)
        super().__init__('\n'.join(self.messages))

@dataclass
class LoadedWorkbook:
    data: pd.DataFrame
    direction: pd.DataFrame | None
    filename: str
    digest: str
    sheets: list[str]
    report: str
    warnings: list[str]
    checks: list[dict]

def load_data(payload: bytes, filename: str) -> LoadedWorkbook:
    if not filename.lower().endswith('.xlsx'):
        raise DataInputError('仅接受 .xlsx 文件；请在Excel中另存为该格式。')
    if not payload or len(payload) > MAX_UPLOAD_BYTES:
        raise DataInputError('文件为空或超过50 MB，请检查文件。')
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            if sum(f.file_size for f in archive.infolist()) > 500 * 1024 * 1024:
                raise DataInputError('工作簿解压后超过500 MB，请删除与本分析无关的大型工作表后再上传。')
        book = pd.ExcelFile(BytesIO(payload), engine='openpyxl')
    except DataInputError:
        raise
    except Exception as exc:
        raise DataInputError('无法读取Excel。文件可能损坏、带密码，或扩展名与真实格式不符。') from exc
    lines = ['航空市场供需分析：数据校验报告', f'文件：{filename}',
             f'SHA256：{hashlib.sha256(payload).hexdigest()}',
             '缺失年份不插值；0值保留；按各指标有效样本规则筛选。']
    notes, checks, frames, fatal = [], [], {}, []
    try:
        if DATA_SHEET not in book.sheet_names:
            raise DataInputError('缺少必需Sheet：Data。请保留原工作表名称。')
        for sheet, fields, code, name, year, values in [
            (DATA_SHEET, DATA_COLUMNS, 'Country Code', 'Country Name', 'Time', ['ASKs','RPKs']),
            (DIRECTION_SHEET, DIRECTION_COLUMNS, 'country_code','country_name','year',['ASK_out','ASK_in'])]:
            if sheet not in book.sheet_names:
                msg = f'缺少Sheet：{sheet}。当前无法运行出发侧（ASK_out）与到达侧（ASK_in）分析（F07、T03、T04）；ASK/RPK分析仍可使用。'
                notes.append(msg)
                lines.append('WARNING ' + msg)
                frames[sheet] = None
                checks.append({'检查项目': sheet, '状态':'缺失 · 部分可用'})
                continue
            frame = pd.read_excel(book, sheet_name=sheet, na_values=['..'])
            missing = [f for f in fields if f not in frame.columns]
            checks.append({'检查项目': sheet, '状态':'存在'})
            if missing:
                fatal.append(f'{sheet} Sheet缺少以下必要字段：{", ".join(missing)}')
                continue
            checks.extend({'检查项目': f'{sheet}.{f}', '状态':'存在'} for f in fields)
            frame = frame[fields].copy()
            blank = frame.isna().all(axis=1)
            lines.append(f'{sheet}: Excel读取{len(frame)}行，移除全空行{int(blank.sum())}行。')
            frame = frame.loc[~blank].copy()
            # Only exact WDI metadata prefixes with ALL other analysis fields empty.
            footer = (frame[name].astype('string').str.startswith(
                ('Data from database:', 'Last Updated:'), na=False)
                & frame[[f for f in fields if f != name]].isna().all(axis=1))
            if footer.any():
                msg = f'{sheet}识别并排除{int(footer.sum())}行WDI来源/更新日期页脚（非观测记录）。'
                notes.append(msg)
                lines.append('WARNING ' + msg)
                frame = frame.loc[~footer].copy()
            if frame.empty:
                fatal.append(f'{sheet}没有观测行。请上传包含数据的工作表。')
                continue
            for col in [code, name]:
                frame[col] = frame[col].replace(r'^\s*$', pd.NA, regex=True)
            # Reject infinity before legacy integer conversion / calculations.
            for col in [year, *values]:
                numeric = pd.to_numeric(frame[col], errors='coerce')
                if numeric.isin([float('inf'), float('-inf')]).any():
                    fatal.append(f'{sheet}.{col}包含无穷值，请改为真实有限数值或留空。')
                    frame.loc[numeric.isin([float('inf'), float('-inf')]), col] = pd.NA
            clean = _clean_and_validate_sheet(frame, sheet, fields, code, name, year, values, lines, fatal)
            frames[sheet] = clean
            for col in values:
                zero = int(clean[col].eq(0).sum())
                if zero:
                    notes.append(f'{sheet}.{col}有{zero:,}个0值：保留原值，不插值；同比要求相邻两年均为正。')
            if clean[code].notna().any() and clean.groupby(code)[name].nunique().gt(1).any():
                notes.append(f'{sheet}存在同一ISO对应多个国家名称；请核对名称一致性，以免方向表按名称拆组。')
        if fatal:
            lines.extend(['校验结论: FAILED', *['ERROR ' + m for m in fatal]])
            raise DataInputError(fatal, '\n'.join(lines))
        lines.append('校验结论: PASSED' if frames.get(DIRECTION_SHEET) is not None else '校验结论: PARTIAL（Data通过，方向Sheet缺失）')
        return LoadedWorkbook(frames[DATA_SHEET], frames.get(DIRECTION_SHEET), filename,
                              hashlib.sha256(payload).hexdigest(), book.sheet_names,
                              '\n'.join(lines), notes, checks)
    finally:
        book.close()
