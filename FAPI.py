"""
author: 周一鸣
date: 2022.4.10
用于FAPI指标构建
"""
import pandas as pd
import datetime

org_predict_data = pd.read_excel('机构预测大全.xlsx')
org_report_data = pd.read_excel('业绩报告.xlsx')

# 此函数用于确定给定日期后最新一期的业绩快报，若无业绩快报，后续计算FTTM时使用上年年报
# 此函数仅针对下载全年数据然后offline模拟时使用，实际操作时，若有wind python接口，可以直接接入查询是否有快报公布
def get_report(first, second, third, date):
    """
    :param first: 一季报公布时间，可能为空
    :param second: 中报公布时间，可能为空
    :param third: 三季报公布时间，可能为空
    :param date: 需要进行判断的时间点
    :return: ret为-1代表未公布任何业绩快报，则计算时使用年报
    """
    ret=-1
    if not pd.isna(third) and date>third:
        ret=3
    elif not pd.isna(second) and date>second:
        ret=2
    elif not pd.isna(first)  and date>first:
        ret=1
    return ret

# 此函数用于根据回溯时间筛选需要用到的业绩预测表格部分
# 仅针对下载全年数据后进行数据清洗，若可以接入wind，可以直接回溯查询
def clean_predict(year, month, counts=6):
    """

    :param year: int型，YYYY格式，当天所处的年份
    :param month: int型，当天所处的月份
    :param counts: int，往前回溯的月份数
    :return: 返回dataframe类型，为清洗后的业绩预测表格
    默认在每月月底计算，故不传入日期
    """
    today = datetime.datetime(year, month + 1, 1)
    # 求出当月月底日期
    today = today - datetime.timedelta(days=1)
    # 因为下载数据的限制，若为每年上半年，则只回溯到当年年初，否则后续使用FTTM公式时需要FY3的值
    if month < counts:
        month = 1
        start_date = datetime.datetime(year, month, 1)
    else:
        month = month - (counts - 1)
        start_date = datetime.datetime(year, month, 1)
        start_date = start_date - datetime.timedelta(days=1)

    org_predict_data_date = org_predict_data.loc[(start_date <= org_predict_data['预测日期']) \
                                                                   & (org_predict_data['预测日期'] <= today)]
    return org_predict_data_date

# 此函数用于计算机构对行业的ROE值
def get_ROE(year,month,counts=6):
    """
    :return: 返回dataframe类型
    """
    today=datetime.datetime(year,month+1,1)
    # 求出当月月底日期
    today=today-datetime.timedelta(days=1)

    org_predict_data_date=clean_predict(year,month,counts)

    #1. 遍历所有股票
    #2. 取三个业绩快报时间和DATE比较
    #3. 确定已公布的利润值(FTTM中的profit_report)和净资产
    org_report_data_date=org_report_data[['证券代码']]
    org_report_data_date=org_report_data_date.copy()
    org_report_data_date['净资产']=''
    org_report_data_date['净利润']=''

    for i in range(org_report_data.shape[0]):
        first_report=org_report_data.loc[i,'业绩快报最新披露日期[报告期] 2021一季']
        sec_report=org_report_data.loc[i,'业绩快报最新披露日期[报告期] 2021中报']
        third_report = org_report_data.loc[i, '业绩快报最新披露日期[报告期] 2021三季']
        rec=get_report(first_report,sec_report,third_report,today)
        if rec==-1:
            # 此种情况未公布任何业绩快报的值，FTTM公式中的profit_report为0
            org_report_data_date.loc[i,'净资产'] = org_report_data.loc[i,'业绩快报.净资产[报告期] 2020年报[单位] 元']
            org_report_data_date.loc[i,'净利润'] = 0
        elif rec==1:
            org_report_data_date.loc[i, '净资产'] = org_report_data.loc[i, '业绩快报.净资产[报告期] 2021一季[单位] 元']
            org_report_data_date.loc[i, '净利润'] = org_report_data.loc[i, '业绩快报.归属母公司股东的净利润[报告期] 2021一季[单位] 元']
        elif rec==2:
            org_report_data_date.loc[i, '净资产'] = org_report_data.loc[i, '业绩快报.净资产[报告期] 2021中报[单位] 元']
            org_report_data_date.loc[i, '净利润'] = org_report_data.loc[i, '业绩快报.归属母公司股东的净利润[报告期] 2021中报[单位] 元']
        elif rec==3:
            org_report_data_date.loc[i, '净资产'] = org_report_data.loc[i, '业绩快报.净资产[报告期] 2021三季[单位] 元']
            org_report_data_date.loc[i, '净利润'] = org_report_data.loc[i, '业绩快报.归属母公司股东的净利润[报告期] 2021三季[单位] 元']

    predict_report=pd.merge(left=org_predict_data_date,right=org_report_data_date,how='inner',\
                            left_on='代码',right_on='证券代码')

    # 因为下载的wind业绩快报数据中很多股票的数据不全，所以对有空值的行全部删掉
    predict_report_notna = predict_report.dropna(axis=0,how="any")
    predict_report_notna = predict_report_notna.sort_values('预测日期', ascending=False)
    # 只取最新一条预测数据
    predict_report_notna = predict_report_notna.drop_duplicates(subset=['研究员','代码'],keep='first')

    # 此处根据ppt中公式计算FTTM，但如果该公司为公布任何业绩快报，这个计算公式会直接用FY1的值替代FTTM
    # 改进点：可以进行判断，如果没有公布任何业绩快报，依然使用wind计算FTTM的方式自然年加权
    predict_report_notna['FTTM']=predict_report_notna['净利润(万元)2021']-predict_report_notna['净利润']+\
                                 predict_report_notna['净利润(万元)2022']*(predict_report_notna['净利润']/predict_report_notna['净利润(万元)2021'])

    # 计算研究员对行业的预测ROE
    industry_analyst_sum=predict_report_notna.groupby(['Wind行业', '机构名称', '研究员'])[['净资产', 'FTTM']].sum()
    industry_analyst_sum=industry_analyst_sum.reset_index()
    industry_analyst_sum['行业_研究员 ROE']=industry_analyst_sum['FTTM']/industry_analyst_sum['净资产']

    # 此处先直接求和，后续可以在研究机构内部对研究员赋权加和算出机构_行业ROE，比如可以考虑研究员报告时效性
    industry_org_sum=industry_analyst_sum.groupby(['Wind行业','机构名称'])['行业_研究员 ROE'].sum()
    industry_org_sum=industry_org_sum.reset_index()
    industry_org_sum.rename(columns={'行业_研究员 ROE':'行业_机构 ROE'}, inplace=True)
    return industry_org_sum

# 此函数根据机构对板块的覆盖度计算机构重要性指标，用于加权处理fapi指数
# 此函数根据上一年的板块净利润和个股上一年净利润进行计算
def get_org_importance(today):
    """

    :param today: datetime类型
    :return: 返回dataframe
    """
    year = int(today.strftime('%Y'))
    month = int(today.strftime('%m'))
    predict_all=clean_predict(year, month)
    predict_all_industry_org = predict_all.groupby(['Wind行业','机构名称'])['净利润(万元)2020'].sum()
    predict_all_industry_org = predict_all_industry_org.reset_index()
    # print(predict_all_industry_org)

    # 导入wind行业分类20年板块净利润
    wind_industry = pd.read_excel('20年板块利润.xlsx')
    org_importance = pd.merge(left=predict_all_industry_org, right=wind_industry, left_on='Wind行业', right_on='板块')
    org_importance['importance'] = org_importance['净利润(万元)2020']/org_importance['净利润(合计)[单位] 元']

    # 分行业对数据进行归一化处理（计算公式同minmaxscaler）
    industry_min_max = org_importance.groupby(['Wind行业'])['importance'].agg(['min', 'max'])
    industry_min_max = industry_min_max.reset_index()
    org_importance_minmax = pd.merge(left=org_importance, right=industry_min_max, on='Wind行业')
    org_importance_minmax['importance_minmax'] = (org_importance_minmax['importance']-org_importance_minmax['min'])/ \
                                                          (org_importance_minmax['max']-org_importance_minmax['min'])
    return org_importance_minmax

# 此函数用于衡量报告时效性指标
# 计算研究员最新一次预测的时间距离此年年报时间的差值，并做年化处理
def get_valid_dates(today):
    """

    :param today: datetime类型
    :return: 返回dataframe
    """
    year = int(today.strftime('%Y'))
    month = int(today.strftime('%m'))
    predict_all = clean_predict(year, month)
    predict_all = predict_all.sort_values('预测日期', ascending=False)
    predict_latest = predict_all.iloc[:,:5].drop_duplicates(subset=['代码', '研究员'], keep='first')
    next_year = datetime.datetime(year+1, 4, 30)
    predict_latest['valid_dates'] = predict_latest.apply(lambda x: (next_year-x['预测日期']).days/365, axis=1)
    return predict_latest

# 此函数用于计算FAPI指数
def get_FAPI(today):
    year=int(today.strftime('%Y'))
    month=int(today.strftime('%m'))
    # 添加判断主要是因为仅下载了一年数据，在实际操作中可以和上年末预测值比较
    if month==1 and month>12:
        print('月份不满足要求')
        exit()
    last_month=month-1
    last_month_ROE = get_ROE(year, last_month)
    month_ROE = get_ROE(year, month)
    ROE_diff = pd.merge(left=month_ROE, right=last_month_ROE, how='left', on=['Wind行业','机构名称'], suffixes=('_now', '_last'))
    ROE_diff = ROE_diff.dropna(axis=0, how='any')
    ROE_diff = ROE_diff.copy()

    # 可以加入和中证800的横向比较
    def get_diff(now, last):
        if now>last and (now-last)/last>0.0001:
            return 1
        else:
            return 0

    ROE_diff['Diff'] = ROE_diff.apply(lambda x: get_diff(x['行业_机构 ROE_now'], x['行业_机构 ROE_last']), axis=1)

    # 此处先做等权处理，后续可以使用报告时效性和机构重要性以及预测准确性进行加权
    ROE_diff_result=ROE_diff.groupby(['Wind行业'])['Diff'].agg(['sum', 'count'])
    ROE_diff_result=ROE_diff_result.reset_index()

    ROE_diff_result['FAPI']=ROE_diff_result['sum']/ROE_diff_result['count']
    ROE_diff_result.sort_values('FAPI', ascending=False, inplace=True)
    print(ROE_diff_result)

if __name__== '__main__':
    dt=datetime.datetime(2021,8,30)
    get_FAPI(dt)