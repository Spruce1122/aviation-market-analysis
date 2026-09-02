import streamlit as st
from core.catalog import MODULES

def navigation():
    st.sidebar.markdown('#### 分析工作台')
    return st.sidebar.radio('分析模块',MODULES,key='module',label_visibility='collapsed')

def fixed_settings_note():
    st.sidebar.caption('固定研究口径：Large前40 / Small后40；方向分析2000—2019；每侧9个极端国家。')
    st.sidebar.caption('上传文件仅在当前会话内存处理，不写入公共目录。')
