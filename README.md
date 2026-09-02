# 航空市场供需分析与可视化系统

可直接部署到Streamlit Community Cloud的Web应用。终端用户只需通过浏览器访问网址，上传`World_Development_Indicators.xlsx`后即可生成F01—F07、A01—A03、T01—T04，并下载PNG、PDF、CSV、XLSX或完整结果ZIP。

## Excel要求

- `Data`：`Country Name`、`Country Code`、`Time`、`ASKs`、`RPKs`。
- `country_year_ask_capacity`：`country_code`、`country_name`、`year`、`ASK_out`、`ASK_in`。
- 保持Sheet名、字段名、单位和ISO口径一致。
- 缺少方向Sheet时，ASK/RPK模块仍可使用，F07、T03、T04会明确跳过。
- 缺失年份不插值，0值保留；负数、无穷值、错误年份和重复国家—年份会被拒绝。

## 数据隔离

- 上传Excel读入当前Streamlit会话的内存，不写入仓库、公共目录或共享结果目录。
- 指标、图形和结果ZIP全部保存在当前会话状态中，不使用跨用户数据缓存。
- 上传新内容时，程序根据SHA256清理旧图形与结果后重新计算。
- 页面中的“清除本次会话数据”可立即释放当前会话对象。
- Matplotlib在`/tmp`中仅保存字体缓存，不包含上传Excel或图表数据。

## 云端稳定渲染

- 正式指标卡、图形和数据表由服务端生成普通HTML或静态PNG，不依赖DataFrame、Metric或Pyplot前端动态组件。
- 图形预览为170 DPI，PNG下载仍为350 DPI，PDF为矢量格式；三者共用同一个Matplotlib Figure。
- 表格预览最多30行（图数据最多100行），完整内容通过CSV/XLSX下载。
- 研究参数固定：Large/Small各40国，方向分析2000—2019、每侧9国，动态最低4个有效年份。
- 国家动态页可单独选择1—30国和年份范围；增长率始终先按完整国家时间序列计算。

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
