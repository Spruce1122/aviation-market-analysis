# 航空市场供需分析 Streamlit 网页

终端用户通过浏览器访问网址、上传 `World_Development_Indicators.xlsx`，即可生成图表、统计表和完整结果ZIP。Python运行环境由云端提供，终端用户无需安装Python。

## 网页结构

左侧仅保留五个一级模块：

1. 数据概览
2. 全样本分析
3. 分国家ASK/RPK分析
4. 出发侧（ASK_out）与到达侧（ASK_in）分析
5. 数据与方法说明

网页保留F01—F07、A01—A03、T01—T04内部编号。F05作为底层历史函数继续保留，由A01指数模式复用，网页不提供F05独立入口。

## Excel要求

- 文件格式：`.xlsx`，最大50MB。
- Sheet `Data`：`Country Name`、`Country Code`、`Time`、`ASKs`、`RPKs`。
- Sheet `country_year_ask_capacity`：`country_code`、`country_name`、`year`、`ASK_out`、`ASK_in`。
- `Data`为必需；缺少方向Sheet时，ASK/RPK模块仍可运行，方向模块显示明确提示。
- 缺失值保持缺失，0值保留；同比仅在相邻年份连续且前后两期均为正时计算。

## Streamlit Community Cloud部署

GitHub仓库根目录应直接包含 `app.py`、`requirements.txt`、`packages.txt`、`runtime.txt`、`.streamlit/`、`core/`、`plots/`、`tables/`、`components/` 和 `utils/`。

1. 将本项目文件上传到GitHub仓库根目录并推送到主分支。
2. 登录 [Streamlit Community Cloud](https://share.streamlit.io/)。
3. 选择 **Create app**，指定GitHub仓库、主分支和入口文件 `app.py`。
4. 点击部署。`requirements.txt`安装Python依赖，`packages.txt`安装Linux中文字体，`.streamlit/config.toml`应用上传限制和安全设置。
5. 后续向同一分支推送代码，现有App会自动重新部署，无需删除App。

终端用户只访问部署网址。上传文件及派生结果保存在当前Streamlit会话内存中；程序不把上传Excel写入项目公共目录，也不跨用户复用结果。会话刷新或失效后，内存数据随之释放。

## Linux云服务器迁移

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

服务器安装Noto CJK字体后运行 `fc-cache -fv`。生产环境建议由Nginx或云负载均衡器提供HTTPS和访问控制。

## 本地开发与测试

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python -m streamlit run app.py
```

批量导出与网页共用相同处理管线：

```bash
python run_batch.py --input sample_data/World_Development_Indicators.xlsx --output results.zip
```

## 隐私、临时文件和异常处理

- 上传文件直接以字节流读取，不保存原始文件。
- 会话缓存键包含文件SHA256和参数；新文件上传后旧分析缓存立即失效。
- Matplotlib只使用系统临时目录保存自身缓存；图表、表格和结果ZIP均在内存生成。
- 输入错误以字段级提示和校验报告呈现；页面不显示服务器堆栈信息。
- CSV/XLSX导出对潜在公式前缀进行转义，降低表格公式注入风险。

## GitHub目录

```text
aviation-market-analysis/
├── .streamlit/config.toml
├── app.py
├── components/
│   ├── chart_info.py
│   ├── download.py
│   ├── pages.py
│   ├── sidebar.py
│   ├── theme.py
│   ├── time_selector.py
│   └── upload_panel.py
├── core/
├── plots/
├── tables/
├── utils/
├── sample_data/World_Development_Indicators.xlsx
├── tests/
├── DATA_AND_FIGURE_GUIDE.md
├── requirements.txt
├── requirements-dev.txt
├── packages.txt
├── runtime.txt
└── README.md
```

完整指标、逐图逐表读法和更新规则见 `DATA_AND_FIGURE_GUIDE.md`。
