from dataclasses import replace
import streamlit as st
from core.catalog import MODULES
from core.config import DEFAULT_CONFIG

def navigation():
    st.sidebar.markdown('#### 分析工作台')
    return st.sidebar.radio('分析模块',MODULES,key='module',label_visibility='collapsed')

def parameters():
    config=st.session_state.setdefault('config',DEFAULT_CONFIG)
    with st.sidebar.expander('分析参数',expanded=False):
        with st.form('analysis_parameters'):
            n_large=st.number_input('Large国家数',1,500,config.n_large,key='large_input')
            n_small=st.number_input('Small国家数',1,500,config.n_small,key='small_input')
            start=st.number_input('ASK方向起始年份',1900,2200,config.direction_start,key='direction_start')
            end=st.number_input('ASK方向结束年份',1900,2200,config.direction_end,key='direction_end')
            top=st.selectbox('方向极端国家：每侧数量',[5,9,10,15],index=[5,9,10,15].index(config.top_direction_n),key='direction_top')
            years=st.number_input('动态指标最低有效年份',2,50,config.min_dynamic_years,key='min_years')
            apply=st.form_submit_button('应用参数',width='stretch')
        if apply:
            candidate=replace(config,n_large=int(n_large),n_small=int(n_small),direction_start=int(start),
                              direction_end=int(end),top_direction_n=int(top),min_dynamic_years=int(years))
            try:
                candidate.validate()
                st.session_state.config=candidate
            except ValueError as exc:
                st.error(str(exc))
    c=st.session_state.config
    if c.n_large==40 and c.n_small==40:
        st.sidebar.caption('报告默认分组：前40 / 后40')
    else:
        st.sidebar.caption(f'自定义分组：前{c.n_large} / 后{c.n_small}')
    st.sidebar.caption('文件仅在当前会话内存处理\n\n更新数据后按文件内容自动重算')
    return c
