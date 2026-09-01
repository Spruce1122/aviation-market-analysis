import streamlit as st
from core.catalog import CHARTS,TABLES
from utils.export import csv_bytes,xlsx_bytes,figure_bytes,results_zip

def chart_downloads(fig,data,stem,key):
    a,b,c=st.columns(3)
    a.download_button('下载 PNG · 350 DPI',figure_bytes(fig),stem+'.png','image/png',key=key+'_png',on_click='ignore',width='stretch')
    b.download_button('下载当前图数据 CSV',csv_bytes(data),stem+'_data.csv','text/csv',key=key+'_csv',on_click='ignore',width='stretch')
    c.download_button('下载 PDF · 矢量图',figure_bytes(fig,'pdf'),stem+'.pdf','application/pdf',key=key+'_pdf',on_click='ignore',width='stretch')

def table_downloads(code,sheet,frame,sheets):
    a,b=st.columns(2)
    a.download_button('下载当前筛选 CSV',csv_bytes(frame),code+'_'+sheet+'.csv','text/csv',key=code+'_csv',on_click='ignore',width='stretch')
    b.download_button('下载完整表 XLSX',xlsx_bytes(sheets),TABLES[code][1]+'.xlsx',
                      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key=code+'_xlsx',on_click='ignore',width='stretch')

def full_download(bundle):
    st.markdown('#### 导出本次完整分析')
    st.caption('包含全部可用图、表、对应数据、校验报告和参数记录；采用当前已应用参数。首次生成需要一些时间。')
    if st.button('生成完整结果 ZIP',key='build_zip'):
        progress=st.progress(0,text='准备导出')
        try:
            st.session_state.results_zip=results_zip(bundle,lambda value,text:progress.progress(value,text=text))
        except Exception:
            st.error('完整结果导出未完成，请检查样本及数据质量后重试。')
            st.session_state.pop('results_zip',None)
        finally:
            progress.empty()
    if 'results_zip' in st.session_state:
        st.download_button('下载 results.zip',st.session_state.results_zip,'results.zip','application/zip',
                           key='results_zip_button',on_click='ignore',type='primary')
