import math
from datetime import timedelta
from math import isnan

import pandas as pd


def compute_monthly_income(df, user_df):
    df = df[df['InTime'] != df['OutTime']]
    df_temp = compute_monthly_tmp_income(df)
    df_family = compute_monthly_family_income(df)
    df_month = compute_monthly_month_income(df, user_df)
    return pd.concat([df_month, df_family, df_temp], axis=0)


def calc_tmp_fee(stay_minutes, in_time):
    if stay_minutes <= 15 or in_time is None:
        return 0

    if stay_minutes <= 1440:
        hours = math.ceil(stay_minutes / 60)
        return min(hours * 5, 30)

    # 超出24小时，递归计算
    days = stay_minutes // 1440
    remainder = stay_minutes % 1440
    return days * 30 + calc_tmp_fee(remainder, in_time + timedelta(days=days))

def calc_family_fee(stay_minutes, in_time):
    if stay_minutes <= 120 or in_time is None:
        return 0

    if stay_minutes <= 720:
        return 5
    elif stay_minutes <= 1440:
        return 10

    # 超出24小时，递归计算
    days = stay_minutes // 1440
    remainder = stay_minutes % 1440
    return (days * 10) + calc_family_fee(remainder, in_time + timedelta(days=days))

def calc_month_fee(row):
    if isnan(row['Order']):
        row['Order'] = 1
    if row['Order'] <= 1:
        return 125  # 第一辆车
    elif row['Order'] == 2:
        return 200  # 第二辆车
    else:
        return 300  # 第三辆车

def compute_monthly_tmp_income(df):
    df = df[df['TypeClass'] == '临时车'].copy()
    df['Fee'] = df.apply(lambda row: calc_tmp_fee(row['StayTime'], row['InTime']), axis=1)
    result = df.groupby(['Year', 'Month', 'YearMonth'])['Fee'].sum().reset_index()
    result['TypeClass'] = '临时车'
    return result

def compute_monthly_family_income(df):
    df = df[df['TypeClass'] == '亲情车'].copy()
    df['Fee'] = df.apply(lambda row: calc_family_fee(row['StayTime'], row['InTime']), axis=1)
    result = df.groupby(['Year', 'Month', 'YearMonth'])['Fee'].sum().reset_index()
    result['TypeClass'] = '亲情车'
    return result

def compute_monthly_month_income(df, user_df):
    df = df[df['TypeClass'] == '月租车'][['Year', 'Month', 'YearMonth', 'CPH']].drop_duplicates()
    df = df.merge(user_df, on='CPH', how='left')
    df['UserName'] = df['UserName'].fillna("")
    df['HomeAddress'] = df['HomeAddress'].fillna("")
    df['Fee'] = df.apply(calc_month_fee, axis=1)
    result = df.groupby(['Year', 'Month', 'YearMonth'])['Fee'].sum().reset_index()
    result['TypeClass'] = '月租车'
    return result

def compute_single_tmp_income(df):
    df = df[df['TypeClass'] == '临时车'].copy()
    df['Fee'] = df.apply(lambda row: calc_tmp_fee(row['StayTime'], row['InTime']), axis=1)
    df = df.groupby(['Year', 'Month', 'YearMonth', 'CPH'])['Fee'].sum().reset_index()
    return df[df['Fee'] > 0]

def compute_single_family_income(df):
    df = df[df['TypeClass'] == '亲情车'].copy()
    df['Fee'] = df.apply(lambda row: calc_family_fee(row['StayTime'], row['InTime']), axis=1)
    df = df.groupby(['Year', 'Month', 'YearMonth', 'CPH'])['Fee'].sum().reset_index()
    return df[df['Fee'] > 0]

def compute_single_month_income(df, user_df):
    df = df[df['TypeClass'] == '月租车'][['Year', 'Month', 'YearMonth', 'CPH']].drop_duplicates()
    df = df.merge(user_df, on='CPH', how='left')
    df['Fee'] = df.apply(calc_month_fee, axis=1)
    df['UserName'] = df['UserName'].fillna("")
    df['HomeAddress'] = df['HomeAddress'].fillna("")
    return df


def compute_single_income(df, user_df):
    df = df[(df['IsInOut'] == True) & (df['TypeClass'] != '免费车')]
    df_temp = compute_single_tmp_income(df)
    df_family = compute_single_family_income(df)
    df_month = compute_single_month_income(df, user_df)
    return df_month, df_family, df_temp