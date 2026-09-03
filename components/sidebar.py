import streamlit as st
from core.catalog import MODULES

def navigation():
    st.sidebar.markdown('#### 分析工作台')
    return st.sidebar.radio('分析模块',MODULES,key='module',label_visibility='collapsed')

def fixed_settings_note():
    st.sidebar.caption('固定分组口径：全样本平均ASK前40为Large、后40为Small。各模块时间范围独立选择。')
    st.sidebar.caption('上传文件仅在当前会话内存处理，不写入公共目录。')
