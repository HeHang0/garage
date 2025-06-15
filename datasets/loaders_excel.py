import os

import pandas as pd


def load_run_from_excel(excel_file, sheet_name='Sheet1'):
    # 1. 读取 Excel 文件
    df = pd.read_excel(excel_file, sheet_name)

    # 2. 字段映射（假设 Excel 中的列是中文，数据库是英文）
    field_mapping = {
        '计费类型': 'CardType',
        '车牌': 'CPH',
        '入口通道': 'InGateName',
        '出口通道': 'OutGateName',
        '出口通道 ': 'OutGateName',
        '入场时间': 'InTime',
        '出场时间': 'OutTime'
    }
    type_mapping = {
        '亲情车': 'MtpB',
        '临时车': 'TmpA',
        '月租车': 'MthA',
        '车库车': 'Fre1'
    }
    df = df.rename(columns=field_mapping)
    df = df[['CardType', 'CPH', 'InGateName', 'OutGateName', 'InTime', 'OutTime']]
    df['InTime'] = pd.to_datetime(df['InTime'])
    df['OutTime'] = pd.to_datetime(df['OutTime'])
    df['CardType'] = df['CardType'].map(type_mapping)
    return df

def load_user_from_excel(excel_file, sheet_name='Sheet1'):
    # 1. 读取 Excel 文件
    df = pd.read_excel(excel_file, sheet_name)

    # 2. 字段映射（假设 Excel 中的列是中文，数据库是英文）
    field_mapping = {
        '姓名': 'UserName',
        '地址': 'HomeAddress',
        '车牌号码': 'CPH'
    }
    df = df.rename(columns=field_mapping)
    df = df[['UserName', 'HomeAddress', 'CPH']]
    df['UserName'] = df['UserName'].fillna('') + '_' + df['HomeAddress'].fillna('')
    return df[['UserName', 'CPH']]

def get_all_excel():
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/bak")
    if not os.path.exists(dir_path):
        return []
    file_path = os.listdir(dir_path)
    return [os.path.join(dir_path, f) for f in file_path if f.lower().endswith(('.xls', '.xlsx'))]

def load_all_run_from_excel(excel_path_list):
    df_list = []
    for excel_path in excel_path_list:
        try:
            df = load_run_from_excel(excel_path, sheet_name=0)
            df_list.append(df)
        except:
            pass
    return df_list

def load_all_user_from_excel(excel_path_list):
    df_list = []
    for excel_path in excel_path_list:
        try:
            df = load_user_from_excel(excel_path, sheet_name=0)
            df_list.append(df)
        except:
            pass
    return df_list

def load_from_excel():
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")
    file_path = os.listdir(dir_path)
    run_df_list = []
    user_df_list = []
    for excel_path in file_path:
        if not excel_path.endswith('.xlsx') and not excel_path.endswith('.xls'):
            continue
        try:
            df = load_run_from_excel(excel_path, sheet_name=0)
            run_df_list.append(df)
        except:
            pass
        try:
            df = load_user_from_excel(excel_path, sheet_name=0)
            user_df_list.append(df)
        except:
            pass
    return run_df_list,user_df_list