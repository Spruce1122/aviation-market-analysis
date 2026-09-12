"""Central navigation, labels, data lineage and interpretation metadata."""

MODULES = [
    "数据概览",
    "全样本分析",
    "分国家ASK/RPK分析",
    "出发侧（ASK_out）与到达侧（ASK_in）分析",
    "数据与方法说明",
]

# Tuple layout is retained for compatibility with the export layer:
# display name, file stem, module, derived fields, short method.
CHARTS = {
    "F02": ("ASK/RPK年度增长率趋势", "F02_ASK_RPK年度增长率中位数趋势", "全样本分析", "ASK_growth、RPK_growth", "相邻年份连续且前后两期均为正时计算同比；ASK与RPK分别按年份取跨国中位数。"),
    "F01": ("ASK与RPK年度增长同步与偏离", "F01_ASK_RPK年度增长同步与偏离", "全样本分析", "ASK_growth、RPK_growth、market_size_group", "仅使用ASK和RPK同比同时有效的国家—年份观测；虚线为y=x。"),
    "F03": ("不同规模市场ASK/RPK增长趋势", "F03_不同规模市场ASK_RPK增长趋势", "全样本分析", "ASK_growth、RPK_growth、market_size_group", "按全样本期平均ASK固定分组，并在各组内按年份分别计算ASK和RPK同比中位数。"),
    "F04": ("不同规模市场ASK/RPK同步性与偏离", "F04_市场规模ASK_RPK同步性与偏离", "全样本分析", "corr、mean_abs_gap_pp、opposite_share_pct", "各组共同同比样本计算Pearson相关系数、平均绝对增长差和反方向变化比例。"),
    "A02": ("PLF年度变化与市场规模比较", "A02_PLF年度变化与市场规模比较", "全样本分析", "PLF、pre_plf、shock_plf、recovery_plf、market_size_group", "三个时期使用同一批国家；第一时期每国取有效PLF中位数，两个比较年份均须有有效PLF。"),
    "A03": ("ASK/RPK年度增长关系分时期观察", "A03_ASK_RPK年度增长关系分时期观察", "全样本分析", "ASK_growth、RPK_growth、growth_gap", "三个面板分别使用各时期共同同比样本并共用坐标范围和y=x参考线。"),
    "A01": ("自选国家ASK/RPK规模与指数比较", "A01_自选国家ASK_RPK规模与指数比较", "分国家ASK/RPK分析", "ASKs、RPKs、base_year、ASK_index、RPK_index", "绝对规模比较原始ASK/RPK；指数模式以所选区间内各国首个ASK与RPK共同正值年份为100。"),
    "F06": ("国家ASK/RPK动态关系类型", "F06_国家ASK_RPK动态关系类型", "分国家ASK/RPK分析", "corr_ask_rpk、mean_abs_growth_gap、n_valid、dynamic_type", "所选时期共同同比样本按国汇总；类型阈值由当前合格国家样本四分位数动态形成。"),
    # Retained for historical reproducibility and reused by A01 index mode.
    "F05": ("代表性国家ASK/RPK指数", "F05_代表性国家ASK_RPK指数走势", None, "base_year、ASK_index、RPK_index", "底层历史绘图函数；网页由A01指数模式复用。"),
    "F07": ("ASK_out与ASK_in方向不对称", "F07_ASK_out_in方向不对称", "出发侧（ASK_out）与到达侧（ASK_in）分析", "mean_ASK_out、mean_ASK_in、R、ln_R、n_years", "所选时期ASK_out和ASK_in共同有效年份分别取均值；R=mean_out/mean_in，ln_R=ln(R)。"),
}

TABLES = {
    "T01": ("ASK/RPK国家排名与排名查询", "T01_ASK_RPK国家排名与排名查询", "所选时期ASK和RPK同时为正的共同年份汇总；加权PLF=ΣRPK/ΣASK×100%。"),
    "T02": ("各国ASK/RPK年度变化方向统计", "T02_各国ASK_RPK年度变化方向统计", "所选时期共同同比国家—年份观测按严格正负号分类，并提供汇总与明细。"),
    "T04": ("ASK_out / ASK_in国家规模排名", "T04_ASK_out_in国家规模排名", "单年使用当年值，多年使用所选时期均值；衡量绝对国际运力规模。"),
    "T03": ("ASK_out / ASK_in极端不对称国家", "T03_ASK_out_in极端不对称国家", "与方向不对称图使用相同时间区间和R、ln(R)口径，按ln(R)两端筛选。"),
}

MODULE_ITEMS = {
    "全样本分析": ["F02", "F01", "F03", "F04", "A02", "A03"],
    "分国家ASK/RPK分析": ["T01", "A01", "F06", "T02"],
    "出发侧（ASK_out）与到达侧（ASK_in）分析": ["T04", "F07", "T03"],
}

HOW_TO_READ = {
    "F02": ["两线长期接近：运力与实际客运量总体同步变化。", "下降阶段RPK低于ASK：需求收缩快于运力撤减。", "恢复阶段RPK高于ASK：需求恢复快于运力重新投放。", "两条线使用各自有效样本，年度国家数可能不同。"],
    "F01": ["45°线上方：RPK增长快于ASK；线下方：ASK增长快于RPK。", "点越靠近45°线，两者变化幅度越同步。", "右上和左下分别表示同时增长、同时下降；右下和左上表示方向相反。", "增长偏离本身不能直接证明运力过剩。"],
    "F03": ["比较三个规模组中ASK与RPK两线的距离、下降幅度和恢复速度。", "某组两线距离更大，表示该组供需增长幅度偏离更明显。", "组间差异描述调整表现，形成原因仍需结合市场背景。"],
    "F04": ["相关系数越高，同步程度越高。", "平均绝对增长差越低，两者增长幅度越接近。", "反方向比例越低，一增一减的情况越少。", "高相关、小差距、低反向比例共同表示较强协调性。"],
    "A02": ["PLF=RPK/ASK×100%，表示既有运力转化为实际客运量的比例。", "PLF提高表示相对利用程度改善；下降表示客运量相对投放运力减弱。", "PLF反映相对利用程度，绝对市场规模需结合ASK和RPK判断。"],
    "A03": ["每个面板对应一个时期；45°线上方表示RPK增长快于ASK。", "比较散点相对45°线的位置，可观察不同时期供需关系的结构变化。", "各时期样本独立筛选，国家数量可能不同。"],
    "A01": ["绝对规模模式比较国家间ASK和RPK实际规模。", "指数模式比较各国相对自身基期的变化速度和轨迹。", "指数大小不能用于比较国家之间的绝对市场规模。"],
    "F06": ["右下区域代表相关性较高、平均偏离较小；左上区域代表协调性较弱。", "点大小表示共同增长有效年份数，颜色表示动态类型。", "分类阈值随时间区间和数据更新重算，国家类型变化属于正常结果。"],
    "T01": ["ASK排名反映运力供给规模，RPK排名反映实际客运运输规模。", "ASK排名更靠前表示该期运力规模相对实际客运规模更靠前。", "运力是否过剩还需结合PLF、趋势与市场背景。"],
    "T02": ["同时增长和同时下降表示同方向变化。", "ASK增长、RPK下降以及ASK下降、RPK增长表示方向偏离。", "统计单位是国家—年份观测。"],
    "T04": ["ASK_out是从该国机场出发国际航段的运力，ASK_in是抵达该国机场国际航段的运力。", "排名反映绝对规模，与方向不对称程度的含义不同。"],
    "F07": ["ln(R)=0表示两侧基本对称；正值表示ASK_out更高；负值表示ASK_in更高。", "绝对值越大，方向不对称越明显。", "R衡量座公里运力供给结构，不能解释为旅客净流量。"],
    "T03": ["表格按ln(R)两端筛选方向结构偏向最明显的国家。", "极端国家表与方向不对称图共用时间区间、样本和计算口径。"],
}

def display_label(code: str) -> str:
    return CHARTS[code][0] if code in CHARTS else TABLES[code][0]

def source_fields(code):
    if code in ("F07", "T03", "T04"):
        return "country_year_ask_capacity", ["country_code", "country_name", "year", "ASK_out", "ASK_in"]
    return "Data", ["Country Name", "Country Code", "Time", "ASKs", "RPKs"]
