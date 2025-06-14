import json
import pickle

from analysis.access_analysis import analyze_single_vehicle, analyze_user, pretty_compare_output
from analysis.behavior_analysis import analyze_activity_patterns
from analysis.plate_pattern import analyze_area_plate
from datasets.loaders import load_parking_records,load_user_info
from datasets.restore import restore_run_from_excel, restore_user_from_excel
from features.preprocess import clean_parking_data, clean_user_data
from analysis.income_analysis import compute_monthly_income, compute_single_income

import pandas as pd
import os

from reports.export_excel import export_to_excel, excel_auto_width  # 可选导出

def get_data():
    df_path = os.path.join("reports", "df.pkl")
    user_path = os.path.join("reports", "user.pkl")
    print("读取数据中...")
    if os.path.exists(df_path):
        df = pickle.load(open(df_path, "rb"))
    else:
        df = load_parking_records()
        excel_df1 = restore_run_from_excel("..\\202412.xls", sheet_name='表一')
        excel_df2 = restore_run_from_excel("..\\202503.xls", sheet_name='表一')
        df = pd.concat([df, excel_df1,excel_df2], ignore_index=True)
    print(f"原始记录数: {len(df)}")

    print("清洗数据中...")
    if os.path.exists(user_path):
        user_df = pickle.load(open(user_path, "rb"))
    else:
        user_df = load_user_info()
        excel_user_df1 = restore_user_from_excel("..\\车库车.xls", sheet_name='数据表')
        excel_user_df2 = restore_user_from_excel("..\\亲情车.xls", sheet_name='数据表')
        excel_user_df3 = restore_user_from_excel("..\\约租车.xls", sheet_name='数据表')
        excel_user_df4 = restore_user_from_excel("..\\月租车.xls", sheet_name='数据表')
        user_df = pd.concat([user_df, excel_user_df1,excel_user_df2,excel_user_df3,excel_user_df4], ignore_index=True)
        user_df = clean_user_data(user_df)
        df = clean_parking_data(df)
        df.to_pickle(df_path)
        user_df.to_pickle(user_path)
    return df, user_df

def area_data(df, _user_df):
    print("统计车牌...")
    province_counts, unknow_cph,car_type_counts,special_df = analyze_area_plate(df, _user_df)
    output_path = os.path.join("reports", "车牌分析.xlsx")
    print(f"导出到: {output_path}...")
    with pd.ExcelWriter(output_path) as writer:
        export_to_excel(province_counts, writer, sheet_name="区域分布")
        export_to_excel(unknow_cph, writer, sheet_name="未知区域")
        export_to_excel(car_type_counts, writer, sheet_name="能源类型")
        export_to_excel(special_df, writer, sheet_name="特殊车牌")
    excel_auto_width(output_path, False)

def behavior_data(df, user_df):
    print("统计行为...")
    b_df = analyze_activity_patterns(df, user_df)
    exception_df = df[(df['IsInOut'] == False) & (df['CPH'].str.len() > 0)].groupby(['CPH', 'IsOnlyIn', 'IsOnlyOut']).size().reset_index(name='Count')
    exception_df['信息'] = exception_df['IsOnlyIn'].apply(lambda x: '异常进入' if x else '异常离开')
    output_path = os.path.join("reports", "行为分析.xlsx")
    print(f"导出到: {output_path}...")
    with pd.ExcelWriter(output_path) as writer:
        print("总览")
        export_to_excel(b_df, writer, sheet_name="总览")
        print("小区车")
        export_to_excel(b_df[b_df['HomeAddress'] != ''].drop(columns=['TypeClass']), writer, sheet_name="小区车")
        print("外部车")
        export_to_excel(b_df[b_df['HomeAddress'] == ''].drop(columns=['HomeAddress', 'TypeClass']), writer, sheet_name="外部车")
        print("月租车")
        export_to_excel(b_df[b_df['TypeClass'] == '月租车'].drop(columns=['TypeClass']), writer, sheet_name="月租车")
        print("临时车")
        export_to_excel(b_df[b_df['TypeClass'] == '临时车'].drop(columns=['TypeClass']), writer, sheet_name="临时车")
        print("免费车")
        export_to_excel(b_df[b_df['TypeClass'] == '免费车'].drop(columns=['TypeClass']), writer, sheet_name="免费车")
        print("异常车辆")
        export_to_excel(exception_df.sort_values(by='Count', ascending=False)[['CPH','Count','信息']], writer, sheet_name="异常车辆")
        print("导出完成")
    excel_auto_width(output_path)

def compute_income(df, user_df):
    print("统计收入...")
    income_df = compute_monthly_income(df, user_df)
    income_month_df, income_tmp_df = compute_single_income(df, user_df)
    # 可选导出结果
    output_path = os.path.join("reports", "收入汇总.xlsx")
    print(f"导出到: {output_path}...")
    with pd.ExcelWriter(output_path) as writer:
        export_to_excel(income_df[income_df['TypeClass'] == '月租车'][['YearMonth', 'Fee']], writer, sheet_name="月租车月度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '临时车'][['YearMonth', 'Fee']], writer, sheet_name="临时车月度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '月租车'].groupby(['Year'])['Fee'].sum().reset_index(), writer, sheet_name="月租车年度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '临时车'].groupby(['Year'])['Fee'].sum().reset_index(), writer, sheet_name="临时车年度收入")

        export_to_excel(income_month_df[['YearMonth', 'CPH', 'Fee']], writer, sheet_name="月租车月度收入明细")
        export_to_excel(income_tmp_df[['YearMonth', 'CPH', 'Fee']], writer, sheet_name="临时车月度收入明细")
        export_to_excel(income_month_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index(), writer, sheet_name="月租车年度收入明细")
        export_to_excel(income_tmp_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index(), writer, sheet_name="临时车年度收入明细")
        export_to_excel(pd.concat([income_month_df, income_tmp_df], axis=0)
                        .groupby(['CPH'])['Fee'].sum().reset_index()
                        .merge(user_df[['CPH', 'UserName', 'HomeAddress']], on='CPH', how='left')
                        .sort_values(by='Fee', ascending=False),
                        writer, sheet_name="收入明细")
    excel_auto_width(output_path, False)

def user_data():
    print("读取数据中...")
    df = load_user_info()
    print(f"原始记录数: {len(df)}")
    print("清洗数据中...")
    df = clean_user_data(df)
    print(df.head())


if __name__ == "__main__":
    _df, _user_df = get_data()

    # compute_income(_df.copy(), _user_df)
    # behavior_data(_df.copy(), _user_df)
    # area_data(_df.copy(), _user_df)
    d = analyze_user(_df, _user_df, '20-1-502')

    # print(json.dumps(d, indent=4, ensure_ascii=False))
    pretty_compare_output(d)
    print("完成")
