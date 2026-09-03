"""Streamlit interface only. All statistics live in core/ and tables/."""
from pathlib import Path
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'aviation_dashboard_mpl'))
import logging
import uuid
import streamlit as st
from core.session import sync_analysis,release_session_data
from core.config import DEFAULT_CONFIG
from core.data_loader import DataInputError
from components.theme import apply_theme,header
from components.upload_panel import upload_panel,empty_panel
from components.sidebar import navigation,fixed_settings_note
from components.pages import overview,chart_page,table_page,dynamic_page,direction_page,period_page,methods_page
from plots.style import setup_plotting_style
from plots.registry import PLOT_LOCK

st.set_page_config(page_title='航空市场供需分析',page_icon='✈',layout='wide',initial_sidebar_state='expanded')
apply_theme()
header()
payload,filename,source_label=upload_panel()
module=navigation()
fixed_settings_note()

if module=='数据与方法说明':
    methods_page()
elif payload is None:
    # Clearing uploader cannot retain a hidden old analysis.
    release_session_data(st.session_state)
    empty_panel()
else:
    try:
        with st.spinner('校验Excel并准备分析数据…'):
            bundle=sync_analysis(st.session_state,payload,filename,DEFAULT_CONFIG)
        st.session_state.source_label=source_label
        if 'font_status' not in st.session_state:
            with PLOT_LOCK:
                st.session_state.font_status=setup_plotting_style(logging.getLogger('aviation_dashboard'))
        if module=='数据概览':overview(bundle,st.session_state.font_status)
        elif module=='统计表':table_page(bundle)
        elif module=='国家动态分析':dynamic_page(bundle)
        elif module=='ASK方向结构':direction_page(bundle)
        elif module=='时期扩展分析':period_page(bundle)
        else:chart_page(bundle,module)
    except DataInputError as exc:
        st.error('当前Excel或参数未通过校验，尚未生成本次分析结果。')
        for message in exc.messages:st.warning(message)
        st.download_button('下载问题报告',exc.report.encode('utf-8'),'validation_error.txt',on_click='ignore')
        st.info('修正数据或应用新的参数后会自动重新计算；不会显示上一份文件的结果。')
    except ValueError:
        logging.getLogger('aviation_dashboard').exception('Analysis result unavailable')
        st.warning('当前结果暂时无法生成，请检查数据覆盖范围。')
    except Exception:
        incident=uuid.uuid4().hex[:10]
        logging.getLogger('aviation_dashboard').exception('Dashboard operation failed [%s]',incident)
        st.error(f'本次操作未完成（诊断编号：{incident}）。请检查Excel格式和样本覆盖；管理员可在部署日志中按编号查找原因。')
