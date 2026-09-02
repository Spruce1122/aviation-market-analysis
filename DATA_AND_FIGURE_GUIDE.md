# 数据与图表使用说明

## 1. 更新Excel后的正确性边界

网页不内置国家排名、市场规模名单、动态分类或历史统计数字。文件内容SHA256变化即视为新数据：清除当前图形、计算结果与导出包，再读取、校验和计算。修改会影响计算的参数也会重新计算。导航、搜索、下载不会重复读取Excel。

正确性前提：原始字段、单位、国家代码和统计覆盖保持一致。程序检验结构与数值规则，无法判断原始数据是否真实，也无法自动识别未声明的单位变化。新增年份请新增行；已有国家—年份应更新原记录，不可追加重复记录。网页研究参数固定，只有“国家动态分析”页的自选国家和年份范围属于展示期交互。

## 2. 原始字段

上传文件名可任意，但必须为`.xlsx`。云部署仓库不包含基准Excel，所有分析均来自当前浏览器会话上传的工作簿。

| Sheet | 原始字段 | 说明 |
|---|---|---|
| Data | Country Name / Country Code | 国家名称 / 三位国家代码 |
| Data | Time | 整数年份 |
| Data | ASKs | 可用座公里，沿用原始单位 |
| Data | RPKs | 收入客公里，必须与ASK单位兼容 |
| country_year_ask_capacity | country_code / country_name / year | 国家代码 / 名称 / 整数年份 |
| country_year_ask_capacity | ASK_out / ASK_in | 出发 / 抵达方向ASK，沿用既有汇总口径 |

国际航段与国内航段的覆盖应在上游数据中确认，网页仅使用已汇总的ASK_out/ASK_in，不能从汇总值重新判断航段类型。其余Sheet不参与计算。

## 3. 校验与清洗

- Data及其5个字段必需；方向Sheet缺失时只开放ASK/RPK分析，F07、T03、T04不可用。
- 同一国家同一年不得重复；名称、代码和年份不得为空，年份须为整数。
- ASKs、RPKs、ASK_out、ASK_in不得为负数、无穷值或非数值文字；`..`作为WDI缺失标记。
- 0保留原值，不转换后插值；完全空白观测行排除。
- 仅当其他分析字段全空时，识别并排除以 `Data from database:`、`Last Updated:` 开头的来源页脚，并写入报告；不自动删掉其他异常行。
- 报告记录非缺失、正值、零值数、代码格式、重复记录、正值年份覆盖及各年覆盖。
- 数据不足时显示原因，不补齐不存在的历史年份。

## 4. 公共指标

| 指标 | 公式 / 规则 |
|---|---|
| ASK_growth | ASK(t)/ASK(t−1)−1；同国年份连续，两个ASK均>0 |
| RPK_growth | RPK(t)/RPK(t−1)−1；同国年份连续，两个RPK均>0；独立计算 |
| common_growth_sample | ASK与RPK同比同时有效；包含增长和下降，不仅是正增长 |
| growth_gap | RPK_growth−ASK_growth；乘100为百分点，不是PLF百分点变化 |
| abs_growth_gap | abs(growth_gap) |
| PLF | RPK/ASK×100；基础字段要求ASK>0且RPK非缺失。疫情样本另限0<PLF≤100% |
| mean_ASK / market_size_group | 全样本期每国非缺失ASK均值；按均值降序、ISO升序；前N_LARGE大型、后N_SMALL小型，其余中型 |
| same / opposite direction | 严格正负判断；零增长未进入严格类别但仍在共同样本分母 |
| ASK_index / RPK_index | 每国首次两项均>0年份为共同基期，各自除以基期水平×100；不跨缺失值插值 |
| corr_ask_rpk | 每国共同同比观测的Pearson相关系数 |
| median_growth_gap | 每国共同同比观测growth_gap中位数 |
| mean_abs_growth_gap | 每国共同同比观测abs_growth_gap均值 |
| opposite_share | 共同同比观测中严格反方向所占比例 |
| growth_gap_std | growth_gap样本标准差，ddof=1 |
| n_valid | 每国共同同比有效年份数 |
| mean_ASK_out / mean_ASK_in | 当前方向分析区间中，两项同时非缺失年份的各自均值；0可参与均值 |
| R / ln_R | 均值均>0时R=mean_ASK_out/mean_ASK_in；ln_R=自然对数ln(R) |
| weighted_PLF | T01共同正值样本的ΣRPK/ΣASK×100 |

PLF精确关系：PLF(t)/PLF(t−1)=(1+RPK_growth)/(1+ASK_growth)。年度普通增长差的正负对应PLF升降，但数值不等于PLF百分点变化。

## 5. 市场规模与国家分类

默认Large40 / Small40。分组使用完整输入的平均ASK。合格国家少于80国时会停止相关分析，不自动改变研究设定。

F06只使用所选区间共同同比有效年数≥4的国家。在这些国家上重算四分位数，按以下顺序互斥分类：

1. 长期高同步型：corr≥Q75且mean_abs_gap≤Q25。
2. ASK相对领先型：median_gap≤Q25。
3. RPK相对领先型：median_gap≥Q75。
4. 高波动型：mean_abs_gap、opposite_share、gap_std任一≥各自Q75。
5. 过渡型：其余国家。

“长期”为沿用图中类型名称，结论只覆盖实际有效年份，不代表更长历史期的因果特征。

## 6. 逐图数据血缘与下载路径

以下路径位于网页下载的 `results.zip` 内。每张图有同名350 DPI PNG及 `figures/vector/` PDF；精确绘图输入见 `figure_data/<编号>_data.csv`。网页显示与下载调用同一Matplotlib Figure。

| 编号 | 侧栏模块 / 图 | Sheet与原始列 | 派生与统计 | ZIP内PNG路径 |
|---|---|---|---|---|
| F01 | ASK–RPK / 年度增长同步与偏离 | Data!Country Name、Country Code、Time、ASKs、RPKs | 共同同比；x=ASK_growth×100，y=RPK_growth×100；颜色=规模；y=x | figures/core/F01_ASK_RPK年度增长同步与偏离.png |
| F02 | ASK–RPK / 年度增长趋势 | Data!Country Name、Country Code、Time、ASKs、RPKs | ASK/RPK独立样本按年中位数 | figures/core/F02_ASK_RPK年度增长率中位数趋势.png |
| F03 | ASK–RPK / 规模市场趋势 | Data!Country Name、Country Code、Time、ASKs、RPKs | 固定规模组内的两类独立同比年度中位数 | figures/core/F03_不同规模市场ASK_RPK增长趋势.png |
| F04 | ASK–RPK / 规模同步与偏离 | Data!Country Name、Country Code、Time、ASKs、RPKs | 各规模组共同国家—年份的Pearson、平均绝对差、反方向占比；N为观测数 | figures/core/F04_市场规模ASK_RPK同步性与偏离.png |
| F05 | 国家动态 / 自选国家指数 | Data!Country Name、Country Code、Time、ASKs、RPKs | 选1—30国；所选区间首次共同正值年为基期；ASK_index、RPK_index | figures/core/F05_自选国家ASK_RPK指数走势.png |
| F06 | 国家动态 / 动态类型 | Data!Country Name、Country Code、Time、ASKs、RPKs | 所选区间重算corr、绝对差和分类阈值；全体合格国绘制，自选国高亮 | figures/core/F06_国家动态关系类型散点图.png |
| F07 | ASK方向 / 方向不对称 | country_year_ask_capacity!country_code、country_name、year、ASK_out、ASK_in | 固定2000—2019成对均值→R→ln_R；自动取两端各9国 | figures/core/F07_ASK_out_in方向不对称.png |
| A01 | 国家动态 / 增长领先比较 | Data!Country Name、Country Code、Time、ASKs、RPKs | 所选区间median_growth_gap两端各10国，去重；n≥4 | figures/additional/A01_国家层面ASK_RPK增长领先比较.png |
| A02 | 疫情 / PLF变化 | Data!Country Name、Country Code、Time、ASKs、RPKs | 严格时期平衡样本；国别疫情前PLF中位数→跨国中位数与Q25/Q75 | figures/additional/A02_疫情冲击前后PLF变化.png |
| A03 | 疫情 / 增长关系 | Data!Country Name、Country Code、Time、ASKs、RPKs | 三时期各自共同同比点，不平衡；同坐标尺度，y=x | figures/additional/A03_疫情前后ASK_RPK增长关系.png |

F01/A03的1%—99%分位及6%留白仅限定画面范围，界外点仍保留在下载数据和统计分母中。

A01保留原报告PNG版式，包括横轴历史遗留的%刻度；实际增长差单位为百分点（pp），轴标题和条形末端已经注明。没有为匹配旧数字更改数据。

## 7. 疫情样本

A02：2016—2019至少有2个有效PLF值，且2020、2021均有效，全部须满足0<PLF≤100%。疫情前取每国有效PLF**中位数**，再跨国汇总。三个时期是同一批国家，不要求疫情前4年全部完整。

A03：疫情前2016—2019、2020、2021分别使用共同同比样本。疫情前点是国家—年份；后两期点是一国一年，不要求相同国家。

## 8. 逐表说明

| 编号 | Sheet / 字段来源 | 筛选、计算与排序 | XLSX工作表与路径 |
|---|---|---|---|
| T01 | Data!Country Name、Country Code、Time、ASKs、RPKs | 2016—2021、两项均>0、至少5个共同水平年份；相同年份均值与加权PLF；排名min法，ISO破同分 | ASK_Top10 / RPK_Top10；tables/T01_主要航空市场ASK_RPK排名.xlsx |
| T02 | Data!Country Name、Country Code、Time、ASKs、RPKs | 全部共同同比样本严格四象限数量/比例，附同反方向小计及零增长校验 | 方向统计 / 校验；tables/T02_ASK_RPK年度变化方向统计.xlsx |
| T03 | country_year_ask_capacity!country_code、country_name、year、ASK_out、ASK_in | 同F07区间、同均值和R/ln_R；按ln_R两端排序 | ln_R最低N国 / ln_R最高N国；tables/T03_ASK_out_in不对称国家.xlsx |
| T04 | 同T03全部5列 | 当前区间mean_ASK_out或mean_ASK_in降序，另一个均值为次排序列 | ASK_out_top10 / ASK_in_top10；tables/T04_ASK_out_in_Top10.xlsx |

T01的mean_ASK使用排名固定期共同年份，与市场规模分组使用全样本期ASK的mean_ASK不同。T02标题沿用原版，表内为所有年份合并统计。

## 9. 国家动态页交互

国家选择器覆盖Data中的全部国家，支持按国家名或ISO检索，最少1国、最多30国。布局随国家数自动变化：1—4国最多2×2，5—6国2×3，7—12国3×4，13—20国4×5，21—30国5×6。F05对每个国家在所选区间重设共同正值基期；若某国无有效基期，网页黄色提示。F06和A01只用所选区间，但增长率仍先在完整序列计算，避免把区间首年错误设为缺失。

## 10. 关键中间数据

`processed_data/` 内保留原有8份CSV：

- country_year_ask_rpk_metrics.csv：原始列、滞后值、同比、共同样本、方向标识、PLF、平均ASK、规模组。
- representative_country_indices.csv：当前代表国家、共同基期、ASK/RPK指数。
- country_dynamic_metrics.csv：国家动态统计、年数与类型。
- dynamic_type_thresholds.csv：本次7个分位数阈值。
- country_ask_direction_metrics.csv：国家区间均值、R、ln_R、有效年数。
- ask_direction_extreme_countries.csv：方向两端国家名单。
- pandemic_plf_balanced_sample.csv：三时期同批国别PLF与规模组。
- t01_market_ranking_eligible_countries.csv：T01全部合格国家及求和、均值、排名。

## 11. 参数与影响

| 参数 | 默认 | 影响 |
|---|---|---|
| N_LARGE / N_SMALL | 40 / 40 | F01、F03、F04、A02组别；网页固定 |
| ASK_DIRECTION_START / END | 2000 / 2019 | F07、T03、T04；网页固定 |
| TOP_DIRECTION_N | 9 | F07、T03每侧数量 |
| MIN_DYNAMIC_VALID_YEARS | 4 | F06、A01；网页固定 |
| 自选国家 | 默认原报告12国，可选1—30国 | F05展示与F06高亮 |
| 国家动态年份 | 完整有效范围，可在该页选择 | F05、F06、A01；先算同比后截取 |
| 疫情期 | 2016—2019 / 2020 / 2021 | A02、A03，固定研究设定 |
| T01排名期 / 最低年数 | 2016—2021 / 5 | T01，固定研究设定 |
| DPI | 350 | 全部PNG质量 |

未来更新会自动改变排名、规模名单、动态分类、增长率及极端国家。疫情定义、排名期和方向默认期不会自动随最新年份移动；这是研究设定。若新年份不在某张图的固定区间内，该图可能保持不变，属于正常结果。

## 12. 复现与测试

默认口径基准：4732行、182国；共同同比777条；Large40 / Medium78 / Small40；PLF平衡113国；方向233国。数字仅用于测试断言，不参与网页计算。

自动化测试覆盖10张图、4组表、同名文件更新、会话隔离、缺失方向Sheet、30国布局、区间基期、动态阈值和静态HTML结果渲染约束。同一数据和默认配置下统计结果一致；不同服务器字体可能产生轻微文字位置差异，不能承诺PNG二进制完全相同。
