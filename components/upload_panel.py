import streamlit as st
from core.config import SAMPLE_FILE

def choose_sample():
    st.session_state['source_mode']='sample'

def choose_upload():
    st.session_state['source_mode']='upload'

def upload_panel():
    st.sidebar.markdown('### 上传原始Excel')
    uploaded=st.sidebar.file_uploader('选择 .xlsx 工作簿',type=['xlsx'],key='workbook_upload',on_change=choose_upload,
                                      help='Data必需；方向分析另需country_year_ask_capacity。最大50 MB。')
    st.sidebar.button('载入报告基准数据',on_click=choose_sample,width='stretch',key='sample_sidebar')
    st.sidebar.divider()
    mode=st.session_state.get('source_mode')
    if mode=='upload' and uploaded is not None:
        return uploaded.getvalue(),uploaded.name,'用户上传'
    if mode=='sample':
        return SAMPLE_FILE.read_bytes(),'World_Development_Indicators.xlsx','报告基准副本'
    return None,None,None

def empty_panel():
    st.markdown('<div class="intro-panel"><div class="section-label">从原始数据开始</div>'
                '<h2>上传一份Excel，展开完整分析</h2>'
                '<p>数据校验、全样本、分国家与出发侧/到达侧分析，在同一个工作台中完成。</p>'
                '<p style="color:#71879b">使用左侧上传框选择数据；或载入原报告基准，先查看全部图表。</p></div>',unsafe_allow_html=True)
    st.button('载入报告基准，开始分析',type='primary',on_click=choose_sample,key='sample_main')
    a,b,c=st.columns(3)
    a.markdown('#### 统一研究图\n按分析逻辑组织并保留复现编号')
    b.markdown('#### 4组统计表\n排序、搜索与Excel下载')
    c.markdown('#### 国家研究\n支持1—30国动态比较')
    with st.expander('查看Excel格式要求',expanded=True):
        st.markdown('**Data**：`Country Name` · `Country Code` · `Time` · `ASKs` · `RPKs`\n\n'
                    '**country_year_ask_capacity**：`country_code` · `country_name` · `year` · `ASK_out` · `ASK_in`\n\n'
                    '保持列名、单位和ISO口径一致。新年份新增观测行；修改已有数值直接覆盖原单元格。')
