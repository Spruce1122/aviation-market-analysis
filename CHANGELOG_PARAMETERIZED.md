# 参数化分析版本变更清单

## 新增文件

- `components/time_selector.py`：独立年份选择、单年/多年模式和文件名时期片段。
- `core/period_analysis.py`：当前时期增长、水平、排名、方向、PLF与T02统计。
- `plots/level_compare.py`：A01及F05单年规模比较。
- `tests/test_period_analysis.py`：计算口径与三个时期场景回归。
- `tests/test_parameterized_pages.py`：F01单年切换及F06单年方法提示页面测试。

## 主要修改文件

- `components/pages.py`：F01—F07、A01—A03、T01—T04全部改为当前参数计算；增加国家年度查询、Top N、统一上下文、参数化下载。
- `components/safe_render.py`、`components/theme.py`：增加当前分析条件信息条。
- `core/session.py`：新文件上传时清除旧图与旧控件参数，保持会话隔离。
- `core/catalog.py`、`components/sidebar.py`、`app.py`：将疫情页改为“时期扩展分析”并接入新路由。
- `core/config.py`：F06最低共同有效同比年份改为3。
- `plots/growth_scatter.py`：F01单年/多年每国一点、可选标签及安全导出。
- `plots/country_index.py`：F05动态布局和标题/图例间距。
- `plots/direction.py`：F07用户国家、时期、排序和单年/多年公式标签。
- `plots/covid.py`：A02年度PLF趋势及A03最多6个年度面板。
- `plots/dynamic_type.py`：F06当前时期高亮国家标签避让。
- `requirements.txt`、`packages.txt`、`.streamlit/config.toml`：Community Cloud依赖、Linux中文字体和上传配置。
- `README.md`、`DEPLOYMENT.md`、`DATA_AND_FIGURE_GUIDE.md`：部署和全图表方法说明。

## 新增或扩展的主要函数

| 函数 | 作用 |
|---|---|
| `select_year_range` | 返回模块独立的start_year、end_year、single/multi模式 |
| `render_analysis_context` | 显示当前国家、时期、模式、有效样本及其他参数 |
| `period_growth_rows` | 在完整序列同比已计算后筛选用户时期 |
| `country_mean_growth` | F01按共同有效年份形成每国一个平均增长点 |
| `level_summary` | 单年水平或多年有效观测平均及覆盖年数 |
| `market_sync_summary` | F04按当前期重算相关、绝对差、反方向比例 |
| `ranking_for_period` | T01单年/多年排名、单位和有效年份 |
| `annual_country_detail` | 国家年度ASK/RPK、X/N排名、同比、PLF |
| `direction_for_period` | 方向数据单年值或多年比率的均值分子/分母 |
| `direction_extremes` | T03按当前ln(R)两端选择用户N |
| `direction_display` | 方向表的时期、动态列名和亿座公里单位 |
| `t02_for_period` | T02当前时期汇总与国家明细 |
| `plf_year_summary` | A02当前时期逐年PLF中位数、四分位和规模组 |
| `plot_f01_period` | F01参数化散点与标签模式 |
| `plot_a01_levels` | A01/F05单年自选国家规模比较 |
| `plot_f07_selected` | F07自选国家及排序 |
| `plot_a02_period`、`plot_a03_period` | 时期扩展图 |

## 参数一致性

图形、页面KPI、数据预览和下载共用当前计算对象。Figure缓存键包含文件digest、国家、开始/结束年份及影响图形的其他参数。上传同名但内容变化的Excel会清理旧控件和旧结果。
