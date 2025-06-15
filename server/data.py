import os
import pickle
from datetime import datetime

import pandas as pd

from analysis.behavior_analysis import analyze_activity_patterns
from analysis.income_analysis import compute_single_income, compute_monthly_income
from analysis.plate_pattern import analyze_area_plate
from datasets.loaders_db import load_user_info, load_parking_records
from datasets.loaders_excel import load_all_user_from_excel, get_all_excel, load_all_run_from_excel
from features.preprocess import clean_user_data, clean_parking_data
from reports.export_excel import export_to_excel, columns_map

_cur_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(_cur_dir, '../data')

def get_data():
    df_path = os.path.join(_data_dir, "df.pkl")
    user_path = os.path.join(_data_dir, "user.pkl")
    excel_file = get_all_excel()
    if os.path.exists(df_path):
        df = pickle.load(open(df_path, "rb"))
    else:
        df = load_parking_records()
        excel_df = load_all_run_from_excel(excel_file)
        excel_df.insert(0, df)
        df = pd.concat(excel_df, ignore_index=True)
        df = clean_parking_data(df)
        df.to_pickle(df_path)

    if os.path.exists(user_path):
        user_df = pickle.load(open(user_path, "rb"))
    else:
        user_df = load_user_info()
        excel_user_df = load_all_user_from_excel(excel_file)
        excel_user_df.insert(0, user_df)
        user_df = pd.concat(excel_user_df, ignore_index=True)
        user_df = clean_user_data(user_df)
        user_df.to_pickle(user_path)
    return df, user_df

def df_to_dict(df):
    # # 获取 columns_map 中与 df.columns 的交集键
    # valid_keys = columns_map.keys() & df.columns
    # # 构造有效的重命名字典
    # valid_columns_map = {k: columns_map[k] for k in valid_keys}
    return df.rename(columns=columns_map).to_dict(orient='records')

def record_data(df, user_df, cph_list, name, start, end):
    if (not cph_list or len(cph_list) == 0) and not name:
        return []
    df = df.merge(user_df, on='CPH', how='left')
    df['UserName'] = df['UserName'].fillna("")
    df['HomeAddress'] = df['HomeAddress'].fillna("")
    if cph_list:
        df = df[df['CPH'].isin(cph_list)]
    if name:
        df = df[(df['HomeAddress'] == name) | (df['UserName'] == name)]
    if start:
        df = df[df['InTime'] >= pd.to_datetime(start)]
    if end:
        df = df[df['OutTime'] <= pd.to_datetime(end)]
    df = df[['CPH', 'TypeClass','InTime','OutTime','InGateName','OutGateName','UserName','HomeAddress']].sort_values(by='InTime', ascending=False)
    df['InTime'] = df['InTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['OutTime'] = df['OutTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df_to_dict(df.head(3000))

def area_data(df, _user_df, return_type='json'):
    now = datetime.now().strftime('%Y%m%d')
    output_path = os.path.join(_data_dir, f"{now}.area.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    province_counts, unknow_cph,car_type_counts,special_df = analyze_area_plate(df, _user_df)
    if return_type == 'json':
        return {
            '区域分布': df_to_dict(province_counts),
            '未知区域': df_to_dict(unknow_cph),
            '能源类型': df_to_dict(car_type_counts),
            '特殊车牌': df_to_dict(special_df)
        }
    with pd.ExcelWriter(output_path) as writer:
        export_to_excel(province_counts, writer, sheet_name="区域分布")
        export_to_excel(unknow_cph, writer, sheet_name="未知区域")
        export_to_excel(car_type_counts, writer, sheet_name="能源类型")
        export_to_excel(special_df, writer, sheet_name="特殊车牌")
    return output_path

def behavior_data(df, user_df, return_type='json'):
    now = datetime.now().strftime('%Y%m%d')
    output_path = os.path.join(_data_dir, f"{now}.behavior.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    pkl_path = os.path.join(_data_dir, f"{now}.behavior.pkl")
    if os.path.exists(pkl_path):
        b_df = pickle.load(open(pkl_path, "rb"))
    else:
        b_df = analyze_activity_patterns(df, user_df)
        b_df.to_pickle(pkl_path)
    exception_df = df[(df['IsInOut'] == False) & (df['CPH'].str.len() > 0)].groupby(['CPH', 'IsOnlyIn', 'IsOnlyOut']).size().reset_index(name='Count')
    exception_df['信息'] = exception_df['IsOnlyIn'].apply(lambda x: '异常进入' if x else '异常离开')
    if return_type == 'json':
        return {
            '总览': df_to_dict(b_df),
            '小区车': df_to_dict(b_df[b_df['HomeAddress'] != ''].drop(columns=['TypeClass'])),
            '外部车': df_to_dict(b_df[b_df['HomeAddress'] == ''].drop(columns=['HomeAddress', 'TypeClass'])),
            '月租车': df_to_dict(b_df[b_df['TypeClass'] == '月租车'].drop(columns=['TypeClass'])),
            '临时车': df_to_dict(b_df[b_df['TypeClass'] == '临时车'].drop(columns=['TypeClass'])),
            '免费车': df_to_dict(b_df[b_df['TypeClass'] == '免费车'].drop(columns=['TypeClass'])),
            '异常车辆': df_to_dict(exception_df.sort_values(by='Count', ascending=False)[['CPH','Count','信息']])
        }
    with pd.ExcelWriter(output_path) as writer:
        export_to_excel(b_df, writer, sheet_name="总览")
        export_to_excel(b_df[b_df['HomeAddress'] != ''].drop(columns=['TypeClass']), writer, sheet_name="小区车")
        export_to_excel(b_df[b_df['HomeAddress'] == ''].drop(columns=['HomeAddress', 'TypeClass']), writer, sheet_name="外部车")
        export_to_excel(b_df[b_df['TypeClass'] == '月租车'].drop(columns=['TypeClass']), writer, sheet_name="月租车")
        export_to_excel(b_df[b_df['TypeClass'] == '临时车'].drop(columns=['TypeClass']), writer, sheet_name="临时车")
        export_to_excel(b_df[b_df['TypeClass'] == '免费车'].drop(columns=['TypeClass']), writer, sheet_name="免费车")
        export_to_excel(exception_df.sort_values(by='Count', ascending=False)[['CPH','Count','信息']], writer, sheet_name="异常车辆")
    return output_path

def compute_income(df, user_df, return_type='json'):
    now = datetime.now().strftime('%Y%m%d')
    output_path = os.path.join(_data_dir, f"{now}.income.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    pkl_path = os.path.join(_data_dir, f"{now}.income.pkl")
    pkl_m_path = os.path.join(_data_dir, f"{now}.income.month.pkl")
    pkl_t_path = os.path.join(_data_dir, f"{now}.income.tmp.pkl")
    if os.path.exists(pkl_path) and os.path.exists(pkl_m_path) and os.path.exists(pkl_t_path):
        income_df = pickle.load(open(pkl_path, "rb"))
        income_month_df = pickle.load(open(pkl_m_path, "rb"))
        income_tmp_df = pickle.load(open(pkl_t_path, "rb"))
    else:
        income_df = compute_monthly_income(df, user_df)
        income_month_df, income_tmp_df = compute_single_income(df, user_df)
        income_df.to_pickle(pkl_path)
        income_month_df.to_pickle(pkl_m_path)
        income_tmp_df.to_pickle(pkl_t_path)
    if return_type == 'json':
        detail_df = pd.concat([income_month_df, income_tmp_df], axis=0).groupby(['CPH'])['Fee'].sum().reset_index().merge(user_df[['CPH', 'UserName', 'HomeAddress']], on='CPH', how='left')
        detail_df['UserName'] = detail_df['UserName'].fillna("")
        detail_df['HomeAddress'] = detail_df['HomeAddress'].fillna("")
        return {
            '月租车月度收入': df_to_dict(income_df[income_df['TypeClass'] == '月租车'][['YearMonth', 'Fee']]),
            '临时车月度收入': df_to_dict(income_df[income_df['TypeClass'] == '临时车'][['YearMonth', 'Fee']]),
            '月租车年度收入': df_to_dict(income_df[income_df['TypeClass'] == '月租车'].groupby(['Year'])['Fee'].sum().reset_index()),
            '临时车年度收入': df_to_dict(income_df[income_df['TypeClass'] == '临时车'].groupby(['Year'])['Fee'].sum().reset_index()),
            '月租车月度收入明细': df_to_dict(income_month_df[['YearMonth', 'CPH', 'Fee']]),
            '临时车月度收入明细': df_to_dict(income_tmp_df[['YearMonth', 'CPH', 'Fee']]),
            '月租车年度收入明细': df_to_dict(income_month_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index()),
            '临时车年度收入明细': df_to_dict(income_tmp_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index()),
            '收入明细': df_to_dict(detail_df.sort_values(by='Fee', ascending=False))
        }
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
    return output_path

def user_data():
    print("读取数据中...")
    df = load_user_info()
    print(f"原始记录数: {len(df)}")
    print("清洗数据中...")
    df = clean_user_data(df)
    print(df.head())