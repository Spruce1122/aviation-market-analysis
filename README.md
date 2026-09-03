# 航空市场供需分析与可视化系统

可直接部署到Streamlit Community Cloud的Web应用。终端用户只需通过浏览器访问网址，上传`World_Development_Indicators.xlsx`后即可生成F01—F07、A01—A03、T01—T04，并下载当前参数对应的PNG、PDF、CSV或XLSX；终端用户不需要安装Python。

## 自主分析能力

- 每个主要模块都有独立的开始年份、结束年份和“恢复默认设置”。
- 单年模式直接使用当年水平；多年模式按所选期有效年份算术平均。
- 同比先在完整国家序列计算，再筛选年份，不会丢失所选区间首年的上一年基数。
- 国家动态页可搜索并选择1—30国；方向页可选择1—30国；排名Top N可输入1至当前有效国家总数。
- 图、KPI、预览和下载使用同一组国家、年份和参数；文件名包含时期、国家数或Top N。
- ASK、RPK和方向ASK的展示值统一换算为亿座公里/亿客公里，底层原始单位保持不变。

## Excel要求

- `Data`：`Country Name`、`Country Code`、`Time`、`ASKs`、`RPKs`。
- `country_year_ask_capacity`：`country_code`、`country_name`、`year`、`ASK_out`、`ASK_in`。
- 保持Sheet名、字段名、单位和ISO口径一致。
- 缺少方向Sheet时，ASK/RPK模块仍可使用，F07、T03、T04会明确跳过。
- 缺失年份不插值，0值保留；负数、无穷值、错误年份和重复国家—年份会被拒绝。

## 数据隔离

- 上传Excel读入当前Streamlit会话的内存，不写入仓库、公共目录或共享结果目录。
- 指标和图形全部保存在当前会话状态中，不使用跨用户数据缓存。
- 上传新内容时，程序根据SHA256清理旧图形与结果后重新计算。
- 页面中的“清除本次会话数据”可立即释放当前会话对象。
- Matplotlib在`/tmp`中仅保存字体缓存，不包含上传Excel或图表数据。

## 云端稳定渲染

- 正式指标卡、图形和数据表由服务端生成普通HTML或静态PNG，不依赖DataFrame、Metric或Pyplot前端动态组件。
- 图形预览为内存PNG，PNG下载为350 DPI，PDF为矢量格式；三者共用同一个Matplotlib Figure。
- 表格预览最多30行（图数据最多100行），完整内容通过CSV/XLSX下载。
- 固定研究口径只有Large/Small各40国和指标公式；方向2000—2019、排名2016—2021仅为控件默认值。
- F06动态类型至少需要3个共同增长有效年份，时间不足时显示方法提示而不调用旧固定区间。

## 仓库结构

```text
aviation-market-dashboard/
├── app.py
├── core/                 # 校验、指标、会话和分析管线
├── plots/                # 原Matplotlib绘图逻辑
├── tables/               # T01—T04
├── components/           # Streamlit页面组件
├── utils/                # 内存导出
├── tests/                # 回归与隔离测试
├── .streamlit/config.toml
├── requirements.txt       # Community Cloud Python依赖
├── packages.txt           # Community Cloud Linux字体
├── Dockerfile
├── docker-compose.yml
├── DEPLOYMENT.md
└── DATA_AND_FIGURE_GUIDE.md
```

仓库不包含原始Excel。`.gitignore`默认排除Excel、ZIP、日志、上传与输出目录。

## 部署

完整步骤见[DEPLOYMENT.md](DEPLOYMENT.md)。Community Cloud创建应用时选择：

```text
Repository: 你的GitHub仓库
Branch: main
Main file path: app.py
Python version: 3.12
```

## 本地维护测试

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python -m streamlit run app.py
```

终端使用者不执行以上命令；他们直接访问部署后的`https://<your-app>.streamlit.app`。
