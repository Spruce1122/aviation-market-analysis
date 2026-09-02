import streamlit as st
from core.session import release_session_data

def choose_upload():
    st.session_state['source_mode']='upload'

def clear_session():
    release_session_data(st.session_state)
    st.session_state['source_mode']=None
    st.session_state['upload_generation']=st.session_state.get('upload_generation',0)+1

def upload_panel():
    st.sidebar.markdown('### 上传原始Excel')
    generation=st.session_state.get('upload_generation',0)
    uploaded=st.sidebar.file_uploader('选择 .xlsx 工作簿',type=['xlsx'],key=f'workbook_upload_{generation}',on_change=choose_upload,
                                      help='Data必需；方向分析另需country_year_ask_capacity。最大50 MB。')
    if uploaded is not None:
        st.sidebar.button('清除本次会话数据',on_click=clear_session,width='stretch',key='clear_session')
    st.sidebar.divider()
    mode=st.session_state.get('source_mode')
    if mode=='upload' and uploaded is not None:
        return uploaded.getvalue(),uploaded.name,'用户上传'
    return None,None,None

def empty_panel():
    st.markdown('<div class="intro-panel"><div class="section-label">从原始数据开始</div>'
                '<h2>上传一份Excel，展开完整分析</h2>'
                '<p>数据校验、供需关系、国家动态与方向结构，在同一个工作台中完成。</p>'
                '<p style="color:#71879b">使用左侧上传框选择数据；网页会在当前会话内完成校验、计算与绘图。</p></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    a.markdown('#### 10张研究图\n统一口径、配色与正式图题')
    b.markdown('#### 4组统计表\n完整排名、筛选与Excel下载')
    c.markdown('#### 国家动态\n自选1—30国及年份区间')
    with st.expander('查看Excel格式要求',expanded=True):
        st.markdown('**Data**：`Country Name` · `Country Code` · `Time` · `ASKs` · `RPKs`\n\n'
                    '**country_year_ask_capacity**：`country_code` · `country_name` · `year` · `ASK_out` · `ASK_in`\n\n'
                    '保持列名、单位和ISO口径一致。新年份新增观测行；修改已有数值直接覆盖原单元格。')
    st.caption('上传文件只在当前浏览器会话的内存中处理；程序不将Excel写入公共目录。')
