# 原始数据、派生指标与图表数据血缘说明

本文档说明 `World_Development_Indicators(4).xlsx` 如何经过Python计算形成全部图表。图表和表格均由 `python run_all.py` 生成。

## 第一部分：原始数据字典

### Excel文件

`input/World_Development_Indicators(4).xlsx`

### Sheet：Data

| Excel原始字段 | 含义 | 本项目用途 |
| --- | --- | --- |
| `Data!Country Name` | 国家英文名称 | 图表国家名称、国家级结果标识 |
| `Data!Country Code` | ISO三位国家代码 | 国家主键、排序、分组、配置名单匹配 |
| `Data!Time` | 自然年份 | 年度排序、连续年份判断、时期筛选 |
| `Data!ASKs` | Available Seat Kilometres，可用座公里 | ASK同比、市场规模、指数、PLF分母、排名 |
| `Data!RPKs` | Revenue Passenger Kilometres，收入客公里 | RPK同比、指数、PLF分子、排名 |

本任务对ASK/RPK的全部计算只调用以上五列。`Data`中的宏观经济、人口、贸易、金融等字段不进入当前分析。

### Sheet：country_year_ask_capacity

| Excel原始字段 | 含义 | 本项目用途 |
| --- | --- | --- |
| `country_year_ask_capacity!country_code` | ISO三位国家代码 | 国家主键与排序 |
| `country_year_ask_capacity!country_name` | 国家英文名称 | 图表和表格国家名称 |
| `country_year_ask_capacity!year` | 自然年份 | 2000—2019年方向分析筛选 |
| `country_year_ask_capacity!ASK_out` | 从该国机场出发的国际航段形成的ASK | 出境方向均值与排名 |
| `country_year_ask_capacity!ASK_in` | 抵达该国机场的国际航段形成的ASK | 入境方向均值与排名 |

本任务的ASK_out/ASK_in图表只调用以上五列。工作簿中的其他Sheet不进入当前代码。

## 第二部分：公共派生变量

### 排序与连续年份

`Data`按 `Country Code`、`Time` 升序排列，`Time`转换为整数。对同一国家，仅当 `Time_t - Time_t-1 = 1` 时认定年份连续。缺失年份不插值，跨年份缺口不计算同比。

### ASK_growth

有效条件：年份连续、`ASKs_t > 0`、`ASKs_t-1 > 0`。

公式：

```text
ASK_growth = ASKs_t / ASKs_t-1 - 1
```

### RPK_growth

有效条件：年份连续、`RPKs_t > 0`、`RPKs_t-1 > 0`。

公式：

```text
RPK_growth = RPKs_t / RPKs_t-1 - 1
```

ASK和RPK分别独立计算同比。某年RPK缺失不会删除同年有效的ASK同比。

### common_growth_sample

共同增长样本同时要求ASK和RPK当期、上期均为正值且年份连续。`growth_gap`、方向类型和ASK—RPK相关性只使用该样本。

### growth_gap与abs_growth_gap

```text
growth_gap = RPK_growth - ASK_growth
abs_growth_gap = abs(growth_gap)
```

`growth_gap > 0`表示RPK增长更快；`growth_gap < 0`表示ASK增长更快。乘以100后单位为百分点。

### same_direction与opposite_direction

- `both_up`：ASK_growth > 0且RPK_growth > 0；
- `both_down`：ASK_growth < 0且RPK_growth < 0；
- `ASK_up_RPK_down`：ASK_growth > 0且RPK_growth < 0；
- `ASK_down_RPK_up`：ASK_growth < 0且RPK_growth > 0；
- `same_direction = both_up or both_down`；
- `opposite_direction = ASK_up_RPK_down or ASK_down_RPK_up`。

增长率恰好等于0的共同样本保留在分母中，并记录为 `zero_growth_unclassified`。

### PLF

当 `ASKs > 0` 且RPK非缺失时：

```text
PLF = RPKs / ASKs × 100
```

变量直接保存百分数值。A02进一步要求 `0 < PLF <= 100`。

### mean_ASK与market_size_group

`mean_ASK`为各国全部非缺失ASK样本期均值。仅对 `mean_ASK > 0` 的国家分组；按 `mean_ASK`降序、ISO代码稳定破同分：

- 前 `N_LARGE=40` 国：`Large`；
- 后 `N_SMALL=40` 国：`Small`；
- 其余国家：`Medium`。

国家名单随数据自动变化。

### ASK_index与RPK_index

对每个代表国家寻找 `ASKs > 0` 且 `RPKs > 0` 的最早年份作为共同基期：

```text
ASK_index = ASKs_t / ASKs_base × 100
RPK_index = RPKs_t / RPKs_base × 100
```

基期两项指数均为100。

### 国家动态指标

对每个国家的共同增长有效样本计算：

- `corr_ask_rpk`：ASK_growth与RPK_growth的Pearson相关系数；
- `median_growth_gap`：growth_gap中位数；
- `mean_abs_growth_gap`：abs_growth_gap算术平均数；
- `opposite_share`：opposite_direction占共同增长有效样本的比例；
- `growth_gap_std`：growth_gap样本标准差，`ddof=1`；
- `n_valid`：共同增长有效年份数。

F06类型识别要求 `n_valid >= 4`。所有分位数由当前合格国家样本动态计算。互斥判定按以下顺序执行：

1. 长期高同步型：`corr_ask_rpk >= corr的Q75` 且 `mean_abs_growth_gap <= 该指标Q25`；
2. ASK相对领先型：`median_growth_gap <= 该指标Q25`；
3. RPK相对领先型：`median_growth_gap >= 该指标Q75`；
4. 高波动型：`mean_abs_growth_gap`、`opposite_share`、`growth_gap_std`中至少一项达到各自Q75；
5. 过渡型：其余合格国家。

实际阈值输出到 `output/processed_data/dynamic_type_thresholds.csv`。

### mean_ASK_out、mean_ASK_in、R与ln_R

默认筛选2000—2019年。每个国家只使用ASK_out与ASK_in同时非缺失的年份：

```text
mean_ASK_out = mean(ASK_out)
mean_ASK_in  = mean(ASK_in)
R            = mean_ASK_out / mean_ASK_in
ln_R         = ln(R)
n_years      = ASK_out与ASK_in共同有效年份数
```

最终保留 `mean_ASK_out > 0` 且 `mean_ASK_in > 0` 的国家。

## 第三部分：逐图说明

## F01 ASK与RPK年度增长同步与偏离

### 图的作用

观察同一国家—年份中运力增长与客运需求增长的同步程度，并比较不同市场规模组的偏离分布。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Name`、`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`ASK_growth`、`RPK_growth`、`common_growth_sample`、`mean_ASK`、`market_size_group`。

### 计算过程

按国家和年份排序，判断年份连续性，计算ASK与RPK同比，计算各国平均ASK并动态划分市场规模组。

### 样本筛选

仅保留共同增长有效样本，且国家具有市场规模组。

### 最终画图字段

- X轴：`ASK_growth × 100`，单位%；
- Y轴：`RPK_growth × 100`，单位%；
- 颜色：`market_size_group`；
- 参考线：`y=x`。

为避免极端值压缩主体分布，程序合并X、Y数据后使用第1和第99百分位形成共同显示范围，并增加6%留白。显示裁切不改变统计样本和中间数据。

### 输出

`output/figures/core/F01_ASK_RPK年度增长同步与偏离.png`

## F02 ASK与RPK年度增长率中位数趋势

### 图的作用

比较各年国家层面ASK和RPK增长率中位数，并保留两项指标各自完整的有效样本。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`ASK_growth`、`RPK_growth`。

### 计算过程

ASK与RPK分别依据自身连续正值计算同比；随后按年份分别计算两者中位数。

### 样本筛选

ASK折线使用ASK_growth非缺失观测；RPK折线使用RPK_growth非缺失观测。两条线不强制使用共同样本。

### 最终画图字段

- X轴：有效增长年份并集；
- Y轴：年度增长率中位数乘100；
- 线条：ASK、RPK；
- 辅助线：`y=0`。

### 输出

`output/figures/core/F02_ASK_RPK年度增长率中位数趋势.png`

## F03 不同规模市场ASK与RPK增长趋势

### 图的作用

比较大型、中型和小型市场中的ASK与RPK年度增长中位数路径。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`ASK_growth`、`RPK_growth`、`mean_ASK`、`market_size_group`。

### 计算过程

先动态划分市场规模组，再按 `market_size_group × Time` 分别计算ASK_growth和RPK_growth中位数。

### 样本筛选

每组内ASK和RPK分别使用各自非缺失增长样本。

### 最终画图字段

- 面板：Large、Medium、Small；
- X轴：年份；
- Y轴：增长率中位数乘100；
- 线条：ASK、RPK；
- 三个面板共享Y轴和全局图例。

### 输出

`output/figures/core/F03_不同规模市场ASK_RPK增长趋势.png`

## F04 不同市场规模国家的ASK–RPK同步性与偏离

### 图的作用

从线性同步性、偏离幅度和反方向变化频率三个维度比较市场规模组。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`ASK_growth`、`RPK_growth`、`abs_growth_gap`、`opposite_direction`、`market_size_group`。

### 计算过程

对每个市场规模组计算ASK_growth与RPK_growth的Pearson相关系数、平均绝对增长差和反方向变化比例。

### 样本筛选

三个指标统一使用共同增长有效样本。N为各组国家—年份观测数。

### 最终画图字段

- 面板A：Pearson相关系数；
- 面板B：`mean(abs_growth_gap) × 100`，单位百分点；
- 面板C：`mean(opposite_direction) × 100`，单位%；
- 柱色：市场规模组；
- 柱顶：指标值和N。

### 输出

`output/figures/core/F04_市场规模ASK_RPK同步性与偏离.png`

## F05 代表性国家ASK与RPK指数走势

### 图的作用

在各国自身共同基期下比较ASK和RPK的累计变化路径，并保留赞比亚作为异常对照。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Name`、`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`base_year`、`ASK_index`、`RPK_index`。

### 计算过程

逐国寻找ASK与RPK同时为正的最早年份，令该年两项指数为100，再使用各期值除以各自基期值。

### 样本筛选

国家名单和顺序来自 `config.py`：CHN、USA、IND、JPN、GBR、DEU、FRA、RUS、BRA、CAN、AUS、ZMB。某项指标后续缺失时，该线自然停止。

### 最终画图字段

- 面板：12个配置国家，4×3排列；
- X轴：`Time`；
- Y轴：`ASK_index`、`RPK_index`；
- 线条：ASK、RPK；
- 全局图例：ASK、RPK。

### 输出

`output/figures/core/F05_代表性国家ASK_RPK指数走势.png`

## F06 国家动态关系类型散点图

### 图的作用

综合展示国家ASK—RPK增长同步性、平均偏离幅度、有效年数和动态类型。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Name`、`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`corr_ask_rpk`、`median_growth_gap`、`mean_abs_growth_gap`、`opposite_share`、`growth_gap_std`、`n_valid`、`dynamic_type`。

### 计算过程

先在共同增长样本上形成国家级动态指标，再对 `n_valid >= 4` 的国家计算当前样本四分位数，并按公共派生变量部分所列优先级识别五类。

### 样本筛选

绘图要求 `n_valid >= 4`、`corr_ask_rpk`非缺失、`mean_abs_growth_gap`非缺失。

### 最终画图字段

- X轴：`corr_ask_rpk`；
- Y轴：`mean_abs_growth_gap × 100`，单位百分点；
- 点大小：`n_valid`；
- 颜色：`dynamic_type`；
- 固定标注：CHN、USA、ZMB；
- 自动标注：平均绝对增长差最高2国和相关系数最低2国，名单随数据变化；
- 标签：adjustText优先，内置确定性避让作为备用。

### 输出

`output/figures/core/F06_国家动态关系类型散点图.png`

`output/processed_data/country_dynamic_metrics.csv`

## F07 ASK_out与ASK_in方向不对称国家比较

### 图的作用

识别2000—2019年国际ASK入境方向与出境方向最不对称的国家。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`country_year_ask_capacity`

原始字段：`country_year_ask_capacity!country_code`、`country_year_ask_capacity!country_name`、`country_year_ask_capacity!year`、`country_year_ask_capacity!ASK_out`、`country_year_ask_capacity!ASK_in`。

### 派生字段

`mean_ASK_out`、`mean_ASK_in`、`R`、`ln_R`、`n_years`。

### 计算过程

在2000—2019年共同有效年份上计算两方向均值、R和ln_R，随后按ln_R升序和降序自动选择两端各9国。

### 样本筛选

要求ASK_out与ASK_in同时非缺失，且国家的两项均值均大于0。

### 最终画图字段

- Y轴：`country_name`；
- X轴：`ln_R`；
- 0线：ASK_out与ASK_in均值相等；
- 颜色：ln_R负值为ASK_in相对占优，正值为ASK_out相对占优；
- 条形末端：实际R值。

### 输出

`output/figures/core/F07_ASK_out_in方向不对称.png`

## A01 国家层面ASK与RPK增长领先比较

### 图的作用

识别长期中位数意义下ASK增长相对领先和RPK增长相对领先最明显的国家。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Name`、`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`growth_gap`、`median_growth_gap`、`n_valid`。

### 计算过程

在共同增长样本上按国家计算growth_gap中位数。

### 样本筛选

要求 `n_valid >= 4`；选择median_growth_gap最小10国和最大10国，ISO代码用于同值稳定排序。

### 最终画图字段

- Y轴：国家英文名称；
- X轴：`median_growth_gap × 100`，单位百分点；
- 左侧：ASK增长相对领先；
- 右侧：RPK增长相对领先。

### 输出

`output/figures/additional/A01_国家层面ASK_RPK增长领先比较.png`

## A02 疫情冲击前后PLF变化

### 图的作用

使用同一批国家比较疫情前、2020年冲击和2021年初步恢复阶段的PLF分布与市场规模差异。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`PLF`、`market_size_group`、国家时期PLF。

### 计算过程

计算PLF并保留 `0 < PLF <= 100`。每国疫情前值为2016—2019年有效PLF中位数；2020和2021分别使用当年PLF。

### 样本筛选

国家在2016—2019年至少有2个有效PLF观测，并同时具有2020和2021有效PLF。三个时期使用同一批国家。

### 最终画图字段

- 面板A：全样本三个时期的中位数、Q25和Q75；
- 面板B：Large、Medium、Small三个组的时期中位数；
- X轴：疫情前、疫情冲击、初步恢复；
- Y轴：PLF百分数。

### 输出

`output/figures/additional/A02_疫情冲击前后PLF变化.png`

`output/processed_data/pandemic_plf_balanced_sample.csv`

## A03 疫情前后ASK与RPK增长关系

### 图的作用

比较疫情前、2020年和2021年的ASK—RPK增长关系及其相对45°线的偏离。

### 原始数据位置

文件：`World_Development_Indicators(4).xlsx`

Sheet：`Data`

原始字段：`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 派生字段

`ASK_growth`、`RPK_growth`、`growth_gap`、`common_growth_sample`。

### 计算过程

计算共同增长样本，并按2016—2019、2020、2021分成三个面板。

### 样本筛选

三个面板均只使用共同增长有效样本。

### 最终画图字段

- X轴：`ASK_growth × 100`；
- Y轴：`RPK_growth × 100`；
- 面板：2016—2019、2020、2021；
- 参考线：`y=x`；
- 标注：CHN、USA、ZMB，每个面板每国只标注绝对增长差最大的一条观测；
- 三个面板使用相同X、Y范围；范围由全部面板X、Y合并数据的第1和第99百分位及6%留白动态确定。

### 输出

`output/figures/additional/A03_疫情前后ASK_RPK增长关系.png`

全部图另有同名PDF保存至 `output/figures/vector/`。

## 第四部分：逐表说明

## T01 主要航空市场ASK/RPK排名

### 原始Sheet与字段

`Data!Country Name`、`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 筛选

固定2016—2021年，ASKs与RPKs均大于0；同国至少5个共同有效年份。

### 计算

- `mean_ASK = mean(ASKs)`；
- `mean_RPK = mean(RPKs)`；
- `weighted_PLF = sum(RPKs) / sum(ASKs) × 100`；
- ASK_rank和RPK_rank在全部合格国家中分别降序计算。

### 排序

分别按ASK_rank和RPK_rank升序截取前10国，ISO代码稳定破同分。

### 输出字段

Country Name、Country Code、n_common_years、mean_ASK、mean_RPK、ASK_rank、RPK_rank、weighted_PLF。

### 输出路径

`output/tables/T01_主要航空市场ASK_RPK排名.xlsx`，Sheet为 `ASK_Top10`、`RPK_Top10`。

CSV：`output/tables/T01_ASK_Top10.csv`、`output/tables/T01_RPK_Top10.csv`。

## T02 ASK/RPK年度变化方向统计

### 原始Sheet与字段

`Data!Country Code`、`Data!Time`、`Data!ASKs`、`Data!RPKs`。

### 筛选

共同增长有效样本。

### 计算

分别统计同时增长、同时下降、ASK增长且RPK下降、ASK下降且RPK增长、同方向合计、反方向合计。比例为类别数除以共同增长有效样本总数乘100。

### 排序

按预设逻辑顺序输出六类。校验Sheet另列总样本、零增长未归类数量和四类合计。

### 输出字段

变化方向、观测数、占有效样本比例（%）。

### 输出路径

`output/tables/T02_ASK_RPK年度变化方向统计.xlsx`

## T03 ASK_out/in不对称国家

### 原始Sheet与字段

`country_year_ask_capacity!country_code`、`country_year_ask_capacity!country_name`、`country_year_ask_capacity!year`、`country_year_ask_capacity!ASK_out`、`country_year_ask_capacity!ASK_in`。

### 筛选

2000—2019年、ASK_out与ASK_in同时非缺失、两项国家均值均大于0。

### 计算

计算mean_ASK_out、mean_ASK_in、R、ln_R和n_years，与F07共用同一个方向指标DataFrame。

### 排序

Sheet一为ln_R最低9国，升序；Sheet二为ln_R最高9国，降序。

### 输出字段

country_name、country_code、mean_ASK_out、mean_ASK_in、R、ln_R、n_years。

### 输出路径

`output/tables/T03_ASK_out_in不对称国家.xlsx`

## T04 ASK_out/in Top10

### 原始Sheet与字段

`country_year_ask_capacity!country_code`、`country_year_ask_capacity!country_name`、`country_year_ask_capacity!year`、`country_year_ask_capacity!ASK_out`、`country_year_ask_capacity!ASK_in`。

### 筛选

与F07、T03相同的2000—2019年processed DataFrame。

### 计算

直接使用mean_ASK_out、mean_ASK_in、R、ln_R和n_years。

### 排序

`ASK_out_top10`按mean_ASK_out降序；`ASK_in_top10`按mean_ASK_in降序。

### 输出字段

国家、ISO、mean_ASK_out、mean_ASK_in、R、ln_R、有效年份数。

### 输出路径

`output/tables/T04_ASK_out_in_Top10.xlsx`

## 第五部分：config.py可修改参数

| 参数 | 默认值 | 影响范围 |
| --- | ---: | --- |
| `N_LARGE` | 40 | F01、F03、F04、A02及processed_data中的市场组 |
| `N_SMALL` | 40 | F01、F03、F04、A02及processed_data中的市场组 |
| `SCATTER_QUANTILE_LOW` | 0.01 | F01、A03显示范围 |
| `SCATTER_QUANTILE_HIGH` | 0.99 | F01、A03显示范围 |
| `SCATTER_LIMIT_MARGIN` | 0.06 | F01、A03坐标留白 |
| `REPRESENTATIVE_COUNTRIES` | 12国固定顺序 | F05国家与面板顺序 |
| `SCATTER_LABEL_COUNTRIES` | CHN、USA、ZMB | A03标注 |
| `F06_FIXED_LABEL_COUNTRIES` | CHN、USA、ZMB | F06固定标注 |
| `F06_AUTO_LABEL_EACH_TAIL` | 2 | F06客观极端标注数 |
| `MIN_DYNAMIC_VALID_YEARS` | 4 | F06国家动态指标最低有效年数 |
| `DYNAMIC_QUANTILE_LOW` | 0.25 | F06类型阈值 |
| `DYNAMIC_QUANTILE_HIGH` | 0.75 | F06类型阈值 |
| `ASK_DIRECTION_START` | 2000 | F07、T03、T04 |
| `ASK_DIRECTION_END` | 2019 | F07、T03、T04 |
| `TOP_DIRECTION_N` | 9 | F07、T03两端国家数 |
| `DIRECTION_RANK_TOP_N` | 10 | T04 |
| `MIN_VALID_GROWTH_YEARS` | 4 | A01 |
| `N_GROWTH_GAP_EXTREMES` | 10 | A01两端国家数 |
| `PANDEMIC_PRE_START` | 2016 | A02、A03 |
| `PANDEMIC_PRE_END` | 2019 | A02、A03 |
| `PANDEMIC_SHOCK_YEAR` | 2020 | A02、A03 |
| `PANDEMIC_RECOVERY_YEAR` | 2021 | A02、A03 |
| `PANDEMIC_PRE_MIN_OBS` | 2 | A02平衡样本 |
| `RANKING_START_YEAR` | 2016 | T01 |
| `RANKING_END_YEAR` | 2021 | T01 |
| `RANKING_MIN_COMMON_YEARS` | 5 | T01 |
| `RANKING_TOP_N` | 10 | T01 |
| `DPI` | 350 | 全部PNG |

## 第六部分：更新数据后的变化

### 会自动变化的结果

- ASK与RPK同比增长率及有效样本数；
- 国家mean_ASK与Large、Medium、Small名单；
- 各年中位数、相关系数、增长差和方向比例；
- 国家动态指标、四分位数阈值与dynamic_type；
- 每个代表国家的共同基期；
- ASK_out/ASK_in方向极端国家；
- ASK、RPK、ASK_out、ASK_in的Top10名单；
- PLF平衡样本和三个时期的统计量。

### 相对固定的研究设定

- 大型市场前40国、小型市场后40国；
- F05代表国家展示名单和顺序；
- 疫情前2016—2019、冲击年2020、初步恢复年2021；
- ASK_out/ASK_in默认分析期2000—2019；
- F07与T03两端各9国；
- T01比较期2016—2021及至少5个共同有效年份。

更新数据后排名、分组和极端国家变化属于正常结果。所有当前数值来自新Excel和程序化筛选规则，代码不会为匹配历史数字而修改原始数据或硬编码结果。

