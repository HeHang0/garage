from math import isnan

import pandas as pd


def compute_monthly_income(df, user_df):
    df = df[df['InTime'] != df['OutTime']]
    df_temp = compute_monthly_tmp_income(df)
    df_month = compute_monthly_month_income(df, user_df)
    return pd.concat([df_month, df_temp], axis=0)


def calc_tmp_fee(row):
    if row['StayTime'] <= 15:
        return 0  # 外来车15分钟内免费
    hours = row['StayTime'] / 60
    if hours > int(hours):
        hours = int(hours) + 1
    else:
        hours = int(hours)
    fee = hours * 5  # 每小时5元
    return min(fee, 30)  # 封顶30元

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
    df['Fee'] = df.apply(calc_tmp_fee, axis=1)
    result = df.groupby(['Year', 'Month', 'YearMonth'])['Fee'].sum().reset_index()
    result['TypeClass'] = '临时车'
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
    df['Fee'] = df.apply(calc_tmp_fee, axis=1)
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
    df_month = compute_single_month_income(df, user_df)
    return df_month, df_temp