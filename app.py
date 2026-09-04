"""Streamlit interface only. All statistics live in core/ and tables/."""
from pathlib import Path
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'aviation_dashboard_mpl'))
import logging
import streamlit as st
from core.session import sync_analysis
from core.data_loader import DataInputError
from components.theme import apply_theme,header
from components.upload_panel import upload_panel,empty_panel
from components.sidebar import navigation,parameters
from components.pages import overview,full_sample_page,country_analysis_page,direction_analysis_page,methods_page
from plots.style import setup_plotting_style,validate_matplotlib_fonts
from plots.registry import PLOT_LOCK

st.set_page_config(page_title='航空市场供需分析',page_icon='✈',layout='wide',initial_sidebar_state='expanded')

@st.cache_resource
def initialize_matplotlib_fonts():
    logger=logging.getLogger('aviation_dashboard')
    with PLOT_LOCK:
        return validate_matplotlib_fonts(logger,setup_plotting_style(logger))

font_status=initialize_matplotlib_fonts()
apply_theme()
header()
if not font_status.get('font_validation_ok',False):
    st.warning('图表中文字体自检未通过：'+font_status.get('font_validation_message','未知字体错误'))
payload,filename,source_label=upload_panel()
module=navigation()
config=parameters()

if module=='数据与方法说明':
    methods_page()
elif payload is None:
    # Clearing uploader cannot retain a hidden old analysis.
    for key in ('bundle','analysis_key','figure_cache','results_zip'):
        st.session_state.pop(key,None)
    empty_panel()
else:
    st.session_state.source_label=source_label
    try:
        with st.spinner('校验Excel并准备分析数据…'):
            bundle=sync_analysis(st.session_state,payload,filename,config)
        if module=='数据概览': overview(bundle,font_status)
        elif module=='全样本分析': full_sample_page(bundle)
        elif module=='分国家ASK/RPK分析': country_analysis_page(bundle)
        elif module=='出发侧（ASK_out）与到达侧（ASK_in）分析': direction_analysis_page(bundle)
    except DataInputError as exc:
        st.error('当前Excel或参数未通过校验，尚未生成本次分析结果。')
        for message in exc.messages:st.warning(message)
        st.download_button('下载问题报告',exc.report.encode('utf-8'),'validation_error.txt',on_click='ignore')
        st.info('修正数据或应用新的参数后会自动重新计算；不会显示上一份文件的结果。')
    except ValueError as exc:
        logging.getLogger('aviation_dashboard').exception('Invalid analysis parameters')
        st.error('当前数据或选择无法完成分析，请检查样本覆盖、年份和参数。')
    except Exception:
        logging.getLogger('aviation_dashboard').exception('Dashboard operation failed')
        st.error('本次操作未完成。请检查Excel格式及安装环境；详细诊断仅记录在本机终端，不在网页暴露。')
