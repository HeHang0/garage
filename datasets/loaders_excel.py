import os
import pickle

import pandas as pd

card_type_mapping = {
    '亲情车': 'MtpB',
    '临时车': 'TmpA',
    '月租车': 'MthA',
    '车库车': 'Fre1'
}

# 定义一个通用的时间解析函数
def parse_time(value):
    try:
        return pd.to_datetime(value)
    except Exception:
        return pd.NaT  # 非法的时间返回 NaT

def load_run_from_excel(excel_file, sheet_name='Sheet1', n_rows=None):
    df_path = excel_file+".pkl"
    if n_rows is None:
        try:
            if os.path.exists(df_path):
                return pickle.load(open(df_path, "rb"))
        except:
            pass
    # 1. 读取 Excel 文件
    if excel_file.endswith('.csv'):
        df = pd.read_csv(excel_file, nrows=n_rows)
    else:
        df = pd.read_excel(excel_file, sheet_name, nrows=n_rows)  # type:pd.DataFrame
    df.columns = df.columns.str.strip()
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
    df = df.rename(columns=field_mapping)
    df = df[['CardType', 'CPH', 'InGateName', 'OutGateName', 'InTime', 'OutTime']]
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    df['InTime'] = df['InTime'].apply(parse_time)
    df['OutTime'] = df['OutTime'].apply(parse_time)
    df['InTime'] = df['InTime'].fillna(df['OutTime'])
    df['OutTime'] = df['OutTime'].fillna(df['InTime'])

    df['CardType'] = df['CardType'].map(card_type_mapping)
    if n_rows is None:
        df.to_pickle(df_path)
    return df

def load_user_from_excel(excel_file, n_rows=None):
    df_path = excel_file+".pkl"
    if n_rows is None:
        try:
            if os.path.exists(df_path):
                return pickle.load(open(df_path, "rb"))
        except:
            pass
    # 1. 读取 Excel 文件
    if excel_file.endswith('.csv'):
        dfs = {"": pd.read_csv(excel_file, nrows=n_rows)}
    else:
        dfs = pd.read_excel(excel_file, sheet_name=None, nrows=n_rows)
    result = pd.DataFrame()
    for name, df in dfs.items():
        df.columns = df.columns.str.strip()
        car_cols = [c for c in df.columns if '车牌号码' in c]
        if len(car_cols) > 1:
            df['UserName'] = df['1、姓名：'].astype(str).fillna('') + '_' + df['4、栋号'].astype(str).fillna('') + '-' + df['5、单元号'].astype(str).fillna('') + '-' + df['6、房间号（如：302）'].astype(str).fillna('')
            df = df.melt(id_vars='UserName', value_vars=car_cols, value_name='CPH')
            df = df.dropna(subset=['CPH'])[['UserName', 'CPH']]
            df['CPH'] = df['CPH'].astype(str).str.replace(r'[\.\s]', '', regex=True).str.replace('(空)', '', regex=False).str.upper()
            df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
        else:
            # 2. 字段映射（假设 Excel 中的列是中文，数据库是英文）
            field_mapping = {
                '姓名': 'UserName',
                # '业主\n姓名': 'UserName',
                '地址': 'HomeAddress',
                '业主房号': 'HomeAddress',
                '车牌号码': 'CPH',
                '人员姓名': 'UserName',
                '家庭住址': 'HomeAddress',
            }
            df = df.rename(columns=field_mapping)
            df = df[['UserName', 'HomeAddress', 'CPH']]
            df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
            df['UserName'] = df['UserName'].fillna('') + '_' + df['HomeAddress'].fillna('')
        df = df[['UserName', 'CPH']]
        result = pd.concat([result, df], ignore_index=True)
    if n_rows is None:
        result.to_pickle(df_path)
    return result

def load_user_address_from_excel(excel_file, n_rows=None):
    df_path = excel_file+".address.pkl"
    if n_rows is None:
        try:
            if os.path.exists(df_path):
                return pickle.load(open(df_path, "rb"))
        except:
            pass
    # 1. 读取 Excel 文件
    if excel_file.endswith('.csv'):
        dfs = {"": pd.read_csv(excel_file, nrows=n_rows)}
    else:
        dfs = pd.read_excel(excel_file, sheet_name=None, nrows=n_rows)
    result = pd.DataFrame()
    for name, df in dfs.items():
        df.columns = df.columns.str.strip()
        # 2. 字段映射（假设 Excel 中的列是中文，数据库是英文）
        field_mapping = {
            '姓名': 'UserName',
            '业主房号': 'HomeAddress',
            '业主\n姓名': 'UserName',
        }
        df['IsTenant'] = df['使用状态'] == '租户租住'
        df = df.rename(columns=field_mapping)
        df = df[['UserName', 'HomeAddress', 'IsTenant']]
        df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
        result = pd.concat([result, df], ignore_index=True)
    if n_rows is None:
        result.to_pickle(df_path)
    return result

def load_coupon_from_excel(excel_file, n_rows=None):
    df_path = excel_file+".coupon.pkl"
    if n_rows is None:
        try:
            if os.path.exists(df_path):
                return pickle.load(open(df_path, "rb"))
        except:
            pass
    # 1. 读取 Excel 文件
    if excel_file.endswith('.csv'):
        df = pd.read_csv(excel_file, nrows=n_rows)
    else:
        df = pd.read_excel(excel_file, sheet_name=0, nrows=n_rows)
    df.columns = df.columns.str.strip()
    car_cols = [c for c in df.columns if '车牌号码' in c]
    if len(car_cols) > 1 and n_rows == 0:
        return df
    df['UserName'] = df['1、姓名：'].astype(str).fillna('') + '_' + df['4、栋号'].astype(str).fillna('') + '-' + df['5、单元号'].astype(str).fillna('') + '-' + df['6、房间号（如：302）'].astype(str).fillna('')
    df = df.melt(id_vars='UserName', value_vars=car_cols, value_name='CPH')
    df = df.dropna(subset=['CPH'])[['UserName', 'CPH']]
    df['CPH'] = df['CPH'].astype(str).str.replace(r'[\.\s]', '', regex=True).str.replace('(空)', '', regex=False).str.upper()
    df[['UserName', 'HomeAddress']] = df['UserName'].str.split('_', n=1, expand=True)
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    if n_rows is None:
        df.to_pickle(df_path)
    return df

def get_all_excel():
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/bak")
    if not os.path.exists(dir_path):
        return []
    file_path = os.listdir(dir_path)
    return [os.path.join(dir_path, f) for f in file_path if f.lower().endswith(('.xls', '.xlsx', '.csv'))]

def load_all_run_from_excel(excel_path_list):
    df_list = []
    for excel_path in excel_path_list:
        try:
            load_run_from_excel(excel_path, sheet_name=0, n_rows=10)
            df = load_run_from_excel(excel_path, sheet_name=0)
            df_list.append(df)
        except:
            pass
    return df_list

def load_address_from_excels(excel_path_list):
    address_path_list = [c for c in excel_path_list if os.path.basename(c).lower().startswith("address")]
    for excel_path in address_path_list:
        try:
            load_user_address_from_excel(excel_path, n_rows=0)
            df = load_user_address_from_excel(excel_path)
            return df
        except:
            pass
    return pd.DataFrame()

def load_coupon_from_excels(excel_path_list):
    coupon_path_list = [c for c in excel_path_list if os.path.basename(c).lower().startswith("coupon")]
    for excel_path in coupon_path_list:
        try:
            load_coupon_from_excel(excel_path, n_rows=0)
            df = load_coupon_from_excel(excel_path)
            return df
        except Exception as e:
            pass
    return pd.DataFrame()

def load_all_user_from_excel(excel_path_list):
    df_list = []
    for excel_path in excel_path_list:
        try:
            load_user_from_excel(excel_path, n_rows=0)
            df = load_user_from_excel(excel_path)
            df_list.append(df)
        except:
            pass
    return df_list

def load_from_excel():
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/bak")
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

def load_family_cph():
    file_path = get_all_excel()
    file_path = [x for x in file_path if os.path.basename(x).startswith("亲情车")]
    cph_set = set()
    for excel_file in file_path:
        if not excel_file.endswith('.xlsx') and not excel_file.endswith('.xls'):
            continue
        try:
            df_path = excel_file+".pkl"
            try:
                if os.path.exists(df_path):
                    df = pickle.load(open(df_path, "rb"))
                    cph_set.update(df['车牌号码'].dropna())
                    continue
            except:
                pass
            if excel_file.endswith('.csv'):
                df = pd.read_csv(excel_file)
            else:
                df = pd.read_excel(excel_file, 0)
            df.columns = df.columns.str.strip()
            df.to_pickle(df_path)
            cph_set.update(df['车牌号码'].dropna())
        except:
            pass
    return cph_set