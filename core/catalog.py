"""Stable output identifiers, filenames and per-chart data lineage."""
CHARTS = {
 'F01': ('年度增长同步与偏离', 'F01_ASK_RPK年度增长同步与偏离', 'ASK–RPK供需关系', 'ASK_growth、RPK_growth、market_size_group', '相邻年份连续，ASK与RPK在两年均大于0。每个点为国家—年份；横纵轴为增长率×100，颜色为市场规模，虚线为y=x。1%—99%分位显示范围不改变统计样本。'),
 'F02': ('ASK/RPK年度增长率趋势', 'F02_ASK_RPK年度增长率中位数趋势', 'ASK–RPK供需关系', 'ASK_growth、RPK_growth', '分别使用ASK独立同比样本、RPK独立同比样本，按年份取跨国中位数。不是加总量增速，也不强制两条线样本相同。年份筛选发生在同比计算之后。'),
 'F03': ('不同规模市场增长趋势', 'F03_不同规模市场ASK_RPK增长趋势', 'ASK–RPK供需关系', 'ASK_growth、RPK_growth、market_size_group', '按全样本期平均ASK固定市场分组；组内各年分别计算ASK和RPK独立同比中位数。显示区间不会重设市场分组。'),
 'F04': ('市场规模同步性与偏离', 'F04_市场规模ASK_RPK同步性与偏离', 'ASK–RPK供需关系', 'ASK_growth、RPK_growth、abs_growth_gap、opposite_direction', '组内合并所有共同增长国家—年份，计算Pearson相关系数、平均绝对增长差×100（百分点）、严格反方向比例×100。N为观测数。零增长保留在分母但不属于严格增减类别。'),
 'F05': ('自选国家ASK/RPK指数走势', 'F05_自选国家ASK_RPK指数走势', '国家动态分析', 'base_year、ASK_index、RPK_index', '在所选区间内，各国首次ASK与RPK同时为正的年份为共同基期；指数=当前值/各自基期值×100。各国基期可不同；缺失不插值，非正值不计算指数。'),
 'F06': ('国家动态关系类型', 'F06_国家动态关系类型散点图', '国家动态分析', 'corr_ask_rpk、mean_abs_growth_gap、n_valid、dynamic_type', '共同同比样本至少达到最低有效年份。横轴为Pearson相关系数，纵轴为平均绝对增长差×100（百分点），点面积对应有效年份数。分类按样本四分位数及明确优先顺序自动计算。'),
 'F07': ('ASK方向不对称', 'F07_ASK_out_in方向不对称', 'ASK方向结构', 'mean_ASK_out、mean_ASK_in、R、ln_R、n_years', '区间内仅用ASK_out和ASK_in同时非缺失的年份计算各自均值（保留0）；均值均为正时R=mean_out/mean_in，ln_R=ln(R)。选ln_R两端国家；重叠国家仅绘制一次。'),
 'A01': ('国家增长领先比较', 'A01_国家层面ASK_RPK增长领先比较', '国家动态分析', 'median_growth_gap、n_valid', '国家共同同比有效年数至少为max(动态指标最低年数,4)。按median(RPK_growth−ASK_growth)选最低和最高各10国，去重。值×100的单位为百分点；原图刻度%沿用基准版，条末pp及轴标题为正确单位。'),
 'A02': ('疫情冲击前后PLF变化', 'A02_疫情冲击前后PLF变化', '疫情扩展分析', 'PLF、pre_plf、shock_plf、recovery_plf、market_size_group', '要求0<PLF≤100%。2016—2019至少2个有效年，且2020/2021均有效；三个时期同一批国家。疫情前先取每国有效年份PLF中位数，再取跨国中位数及25%—75%分位区间。'),
 'A03': ('疫情前后ASK/RPK增长关系', 'A03_疫情前后ASK_RPK增长关系', '疫情扩展分析', 'ASK_growth、RPK_growth、growth_gap', '分别绘制2016—2019、2020和2021共同同比样本；不要求时期之间平衡。三个面板同一尺度、同一y=x参考线。上方表示RPK增速高于ASK，与PLF上升对应。'),
}
TABLES = {
 'T01': ('主要航空市场ASK/RPK排名','T01_主要航空市场ASK_RPK排名', '2016—2021内ASK、RPK同时为正至少5年；共同年份均值排名，min法处理并列，ISO破同分。加权PLF=ΣRPK/ΣASK×100。'),
 'T02': ('ASK/RPK年度变化方向','T02_ASK_RPK年度变化方向统计', '合并全部共同同比国家—年份，统计严格正负四象限及同/反方向小计。末两行是小计，不可与前四行相加；零增长计入分母但不进入严格增减类别。'),
 'T03': ('ASK方向极端不对称国家','T03_ASK_out_in不对称国家', '使用当前方向分析区间，按ln_R最低/最高分别展示，与F07一致。'),
 'T04': ('ASK_out / ASK_in Top10','T04_ASK_out_in_Top10', '按当前区间mean_ASK_out或mean_ASK_in排序，各取10国；衡量绝对规模，与ln_R不对称程度不同。'),
}
MODULES = ['数据概览','ASK–RPK供需关系','国家动态分析','ASK方向结构','疫情扩展分析','统计表','数据与方法说明']

def source_fields(code):
    if code in ('F07','T03','T04'):
        return 'country_year_ask_capacity', ['country_code','country_name','year','ASK_out','ASK_in']
    return 'Data', ['Country Name','Country Code','Time','ASKs','RPKs']
