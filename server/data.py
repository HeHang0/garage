import hashlib
import os
import pickle
from datetime import datetime
import time

import pandas as pd

from analysis.behavior_analysis import analyze_activity_patterns
from analysis.income_analysis import compute_single_income, compute_monthly_income
from analysis.plate_pattern import analyze_area_plate
from datasets.loaders_db import load_user_info, load_parking_records
from datasets.loaders_excel import load_all_user_from_excel, get_all_excel, load_all_run_from_excel, load_family_cph, \
    load_address_from_excels, load_coupon_from_excels, card_type_mapping
from features.preprocess import clean_user_data, clean_parking_data, format_minutes_chinese, normalize_address
from reports.export_excel import export_to_excel, columns_map

_cur_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(_cur_dir, '../data')

def get_data():
    df_path = os.path.join(_data_dir, "df.pkl")
    user_path = os.path.join(_data_dir, "user.pkl")
    address_path = os.path.join(_data_dir, "address.pkl")
    coupon_path = os.path.join(_data_dir, "coupon.pkl")
    excel_file = get_all_excel()
    if os.path.exists(df_path):
        df = pickle.load(open(df_path, "rb"))
    else:
        df = load_parking_records()
        excel_df = load_all_run_from_excel(excel_file)
        excel_df.insert(0, df)
        df = pd.concat(excel_df, ignore_index=True)
        family_cph = load_family_cph()
        df = clean_parking_data(df, family_cph)
        df.to_pickle(df_path)

    if os.path.exists(address_path):
        address_df = pickle.load(open(address_path, "rb"))
    else:
        address_df = load_address_from_excels(excel_file)
        address_df['HomeAddress'] = address_df['HomeAddress'].apply(normalize_address)
        address_df.to_pickle(address_path)

    if os.path.exists(user_path):
        user_df = pickle.load(open(user_path, "rb"))
    else:
        user_df = load_user_info()
        excel_user_df = load_all_user_from_excel(excel_file)
        excel_user_df.insert(0, user_df)
        user_df = pd.concat(excel_user_df, ignore_index=True)
        user_df = clean_user_data(user_df)
        user_df['CPH'] = user_df['CPH'].str.upper().replace('(空)', '', regex=False)
        user_df['HomeAddress'] = user_df['HomeAddress'].apply(normalize_address)
        user_df = user_df.drop(columns=['UserName'])
        user_df = user_df.merge(address_df[['UserName','HomeAddress']], on='HomeAddress', how='left')
        user_df['UserName'] = user_df['UserName'].fillna("")
        user_df_empty = user_df[user_df['HomeAddress'] == '0-0-0']
        user_df = user_df[user_df['HomeAddress'] != '0-0-0']
        user_df_empty['HomeAddress']= ""
        rows_to_add = user_df_empty[~user_df_empty['CPH'].isin(user_df['CPH'])]
        user_df = pd.concat([user_df, rows_to_add], ignore_index=True)
        user_df.to_pickle(user_path)
    if os.path.exists(coupon_path):
        coupon_df = pickle.load(open(coupon_path, "rb"))
    else:
        coupon_df = load_coupon_from_excels(excel_file)
        coupon_df.to_pickle(coupon_path)
    return df, user_df, address_df, coupon_df

def df_to_dict(df):
    # # 获取 columns_map 中与 df.columns 的交集键
    # valid_keys = columns_map.keys() & df.columns
    # # 构造有效的重命名字典
    # valid_columns_map = {k: columns_map[k] for k in valid_keys}
    df = df.rename(columns=columns_map)
    return {
        "data": df.values.tolist(),
        "columns": df.columns.tolist()
    }

def record_data(df, user_df, cph_list, name, start, end, date, abnormal):
    if (not cph_list or len(cph_list) == 0) and not name:
        return []
    if start:
        df = df[df['InTime'] >= pd.to_datetime(start)]
    if end:
        df = df[df['OutTime'] <= pd.to_datetime(end)]
    if cph_list:
        df = df[df['CPH'].isin(cph_list)]
    if date:
        date = date[:10]
        df = df[df['InTime'] >= pd.to_datetime(f'{date} 00:00:00')]
        df = df[df['InTime'] <= pd.to_datetime(f'{date} 23:59:59')]
    if abnormal:
        df = df[(df['InTime'] == df['OutTime']) | df['InTime'].isnull()  | df['OutTime'].isnull() | ((df['OutTime'] - df['InTime']) < pd.Timedelta(minutes=1))]
    df = df.merge(user_df, on='CPH', how='left')
    df['UserName'] = df['UserName'].fillna("")
    df['HomeAddress'] = df['HomeAddress'].fillna("")
    if name:
        df = df[(df['HomeAddress'] == name) | (df['UserName'] == name)]
    df = df[['CPH', 'TypeClass','InTime','OutTime', 'StayText','InGateName','OutGateName','UserName','HomeAddress']].sort_values(by='InTime', ascending=False)
    df['InTime'] = df['InTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['OutTime'] = df['OutTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df_to_dict(df.head(5000))

def get_timestamp_text(*args):
    has_valid = any(arg not in (None, '') for arg in args)
    if not has_valid:
        return datetime.now().strftime('%Y%m%d')
    return md5_string(''.join(str(arg) if arg not in (None, '') else '' for arg in args))

def area_data(df, _user_df, start, end, return_type='json'):
    timestamp = get_timestamp_text(start, end)
    output_path = os.path.join(_data_dir, f"cache.{timestamp}.area.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    if start:
        df = df[df['InTime'] >= pd.to_datetime(start)]
    if end:
        df = df[df['OutTime'] <= pd.to_datetime(end)]
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

def user_data(df, user_df, address_df, coupon_df, order, start, end, return_type='json'):
    timestamp = get_timestamp_text(start, end, order)
    output_path = os.path.join(_data_dir, f"cache.{timestamp}.user.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    # ========== Step 1. 聚合 CPH ==========
    # 用户车辆表：按住址聚合车牌
    user_cph = user_df.groupby('HomeAddress', as_index=False).agg(
        CPH=('CPH', lambda x: ','.join(sorted({v for v in x if v}))),   # 去空并去重后排序再拼接
        CPHCount=('CPH', lambda x: len({v for v in x if v}))
    )

    # 问卷表：按住址聚合问卷车牌
    coupon_cph = coupon_df.groupby('HomeAddress', as_index=False)['CPH'].agg(lambda x: ','.join(sorted(set(x))))

    # ========== Step 2. 合并住户信息 ==========
    # 从 address_df 出发（它是 HomeAddress 唯一的主表）
    merged = address_df.copy()
    if merged[(merged['HomeAddress'] == '') | (merged['HomeAddress'] == '0-0-0')].empty:
        # 构造一行空记录
        empty_row = pd.DataFrame([{
            'UserName': '未绑定住户车辆',
            'HomeAddress': '0-0-0',
            'CPH': '',
            'IsTenant': False,
            'CouponCPH': '',
            'HasCoupon': False
        }])
        # 追加到 merged
        merged = pd.concat([merged, empty_row], ignore_index=True)

    # 合并 user_df 的用户名（后面用来补缺）
    user_name_map = user_df[['HomeAddress', 'UserName']].drop_duplicates('HomeAddress')
    coupon_name_map = coupon_df[['HomeAddress', 'UserName']].drop_duplicates('HomeAddress')

    # 按优先级补全：address_df → user_df → coupon_df
    merged = merged.merge(user_name_map, on='HomeAddress', how='left', suffixes=('', '_user'))
    merged = merged.merge(coupon_name_map, on='HomeAddress', how='left', suffixes=('', '_coupon'))

    merged['UserName'] = merged['UserName'].fillna(merged['UserName_user'])
    merged = merged.rename(columns={
        'UserName_coupon': 'CouponUserName'
    })
    # 清理多余列
    merged = merged[['UserName', 'HomeAddress', 'IsTenant', 'CouponUserName']]

    # ========== Step 3. 合并 CPH 信息 ==========
    merged = merged.merge(user_cph, on='HomeAddress', how='left')  # 用户车牌
    merged = merged.merge(coupon_cph.rename(columns={'CPH': 'CouponCPH'}), on='HomeAddress', how='left')

    # ========== Step 4. 生成 HasCoupon ==========
    merged['HasCoupon'] = merged['CouponCPH'].notna() & (merged['CouponCPH'] != '')
    # ========== Step 5. 排列列顺序 ==========
    merged = merged[['UserName', 'HomeAddress', 'CPH', 'CPHCount', 'IsTenant', 'CouponCPH', 'CouponUserName', 'HasCoupon']]
    # ========== Step 6. 可选：填充空值 ==========
    merged = merged.fillna({'UserName': '', 'CouponUserName': '', 'CPH': '', 'CouponCPH': '', 'IsTenant': False})
    merged['UserNameConsistency'] = merged['UserName'] == merged['CouponUserName']
    merged['UserNameConsistency'] = merged['UserNameConsistency'].map({True: '是', False: '否'})
    merged['HasCoupon'] = merged['HasCoupon'].map({True: '是', False: '否'})
    merged['IsTenant'] = merged['IsTenant'].map({True: '是', False: '否'})
    merged['HomeAddress'] = merged['HomeAddress'].apply(normalize_address)
    summary_df = get_summary(df, user_df, start, end)
    merged = merged.merge(summary_df, on='HomeAddress', how='left')
    merged['VisitCount'] = merged['VisitCount'].fillna(0)
    merged['CPHCount'] = merged['CPHCount'].fillna(0)
    order_by = [order]
    ascending = False
    if order == 'HomeAddress':
        merged[['building', 'unit', 'room']] = merged['HomeAddress'].str.split('-', expand=True).astype(int)
        order_by = ['building', 'unit', 'room']
        ascending = True
    merged = merged.sort_values(by=order_by, ascending=ascending).reset_index(drop=True)
    if order == 'HomeAddress':
        merged = merged.drop(columns=['building', 'unit', 'room'])

    merged.loc[merged['HomeAddress'] == '0-0-0', 'HomeAddress'] = ''
    if return_type == 'json':
        return df_to_dict(merged)
    else:
        with pd.ExcelWriter(output_path) as writer:
            export_to_excel(merged, writer, sheet_name="住户信息")
        return output_path


def get_summary(df, user_df, start, end):
    if start:
        df = df[df['InTime'] >= pd.to_datetime(start)]
    if end:
        df = df[df['OutTime'] <= pd.to_datetime(end)]
    # --- Step 5. 匹配 HomeAddress ---
    summary = df.merge(
        user_df[['CPH', 'HomeAddress']], on='CPH', how='left'
    )
    summary['HomeAddress'] = summary['HomeAddress'].fillna('0-0-0')
    summary = summary.groupby('HomeAddress').agg(
        VisitCount=('HomeAddress', 'count'),
    ).reset_index()
    summary['HomeAddress'] = summary['HomeAddress'].apply(normalize_address)
    # --- Step 7. 排列列顺序 ---
    return summary[['VisitCount', 'HomeAddress']]

def first_of_list(lst, default_value=None):
    """
    返回列表的第一个有效值；
    如果列表为空、为None，或第一个元素为空(None或空字符串)，则返回默认值。
    """

    # if not lst:  # None 或 空列表
    #     return default_value
    for first in lst:
        if first not in (None, ''):
            return first
    return default_value

def md5_string(s: str) -> str:
    """
    返回字符串 s 的 MD5 值（32 位小写十六进制）
    """
    # 注意需要先编码成字节
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def calc_true_len(lst):
    result = 0
    for v in lst:
        if v:
            result += 1
    return result

def cph_data(df, user_df, address_df_origin, coupon_df, order, start, end, return_type='json'):
    timestamp = get_timestamp_text(start, end, order)
    df_path = os.path.join(_data_dir, f"cache.{timestamp}.cph.pkl")
    last_ym_df_path = os.path.join(_data_dir, f"cache.{timestamp}.cph.max.date.pkl")
    output_path = os.path.join(_data_dir, f"{timestamp}.cph.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    if start:
        df = df[df['InTime'] >= pd.to_datetime(start)]
    if end:
        df = df[df['OutTime'] <= pd.to_datetime(end)]

    if os.path.exists(last_ym_df_path):
        last_ym_df = pickle.load(open(last_ym_df_path, "rb"))
    else:
        last_ym_df = df.groupby(['CPH', 'YearMonth'], as_index=False).agg(
            LastInOutTime=('OutTime', lambda x: max(x))
        )
        last_ym_df.to_pickle(last_ym_df_path)

    idx = last_ym_df.groupby('CPH')['LastInOutTime'].idxmax()
    last_df = last_ym_df.loc[idx]
    last_df = last_df[['CPH', 'LastInOutTime']]
    last_df['LastInOutTime'] = last_df['LastInOutTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    last_ym_df['LastInOutTime'] = last_ym_df['LastInOutTime'].dt.strftime('%Y-%m-%d %H:%M:%S')

    cph_date_path = os.path.join(_data_dir, f"cph_date.pkl")
    if os.path.exists(cph_date_path):
        cph_date_df = pickle.load(open(cph_date_path, "rb"))
    else:
        cph_date_df = df[['CPH', 'Date', 'YearMonth']].drop_duplicates(subset=['CPH', 'Date', 'YearMonth'])
        cph_date_df = cph_date_df.groupby(['CPH', 'YearMonth'], as_index=False).agg(
            InOutDays=('CPH', lambda x: len(x))
        )
        cph_date_df.to_pickle(cph_date_path)

    if os.path.exists(df_path):
        df = pickle.load(open(df_path, "rb"))
    else:
        df = df[['TypeClass', 'CPH', 'YearMonth', 'StayTime', 'IsOnlyIn', 'IsOnlyOut', 'IsDayIn', 'IsDayOut', 'IsInOut']]
        df = df.groupby(['CPH', 'YearMonth'], as_index=False).agg(
            TypeClass=('TypeClass', first_of_list),
            StayTime=('StayTime', lambda x: sum(x)),
            VisitCount=('CPH', lambda x: len(x)),
            InOutCount=('IsInOut', calc_true_len),
            InCount=('IsOnlyIn', calc_true_len),
            OutCount=('IsOnlyOut', calc_true_len),
            DayInCount=('IsDayIn', calc_true_len),
            DayOutCount=('IsDayOut', calc_true_len)
        )
        df['InCount'] = df['InCount'] + df['InOutCount']
        df['OutCount'] = df['OutCount'] + df['InOutCount']
        df['NightInCount'] = df['InCount'] - df['DayInCount']
        df['NightOutCount'] = df['OutCount'] - df['DayOutCount']
        address_df = user_df[['CPH', 'HomeAddress']].sort_values(by=['HomeAddress'], ascending=False).reset_index(drop=True)
        address_df = address_df.groupby('CPH', as_index=False).agg(
            HomeAddress=('HomeAddress', first_of_list)
        )
        user_df = user_df[['HomeAddress', 'UserName']].sort_values(by=['UserName'], ascending=False).reset_index(drop=True)
        user_df = user_df.groupby('HomeAddress', as_index=False).agg(
            UserName=('UserName', first_of_list)
        )
        # --- Step 5. 匹配 HomeAddress ---
        df = df.merge(
            address_df, on='CPH', how='left'
        )
        df = df.merge(
            user_df, on='HomeAddress', how='left'
        )
        df['HomeAddress'] = df['HomeAddress'].fillna('')
        df['UserName'] = df['UserName'].fillna('')
        df['TypeClass'] = df['TypeClass'].fillna('')
        df.loc[df['HomeAddress'] == '0-0-0', 'HomeAddress'] = ''
        df = df[['CPH', 'YearMonth', 'TypeClass', 'HomeAddress', 'UserName', 'StayTime', 'VisitCount', 'InCount', 'OutCount', 'DayInCount', 'DayOutCount', 'NightInCount', 'NightOutCount']]
        df.to_pickle(df_path)
    year_month = df[['YearMonth']].drop_duplicates('YearMonth').sort_values(by='YearMonth', ascending=True).values.tolist()
    year_month.insert(0, ['汇总'])
    df_name_arr = []
    for item_arr in year_month:
        item = item_arr[0]
        if item != '汇总':
            df_item = df[df['YearMonth'] == item].copy()
            df_item = df_item.drop(columns=['YearMonth'])
            df_item = df_item.merge(
                last_ym_df[last_ym_df['YearMonth'] == item][['CPH', 'LastInOutTime']], on='CPH', how='left'
            )
            cph_date_df_month = cph_date_df[cph_date_df['YearMonth'] == item].groupby(['CPH'], as_index=False).agg(
                InOutDays=('InOutDays', lambda x: sum(x))
            )
        else:
            df_item = df.groupby(['CPH', 'TypeClass', 'HomeAddress', 'UserName'], as_index=False)[['StayTime', 'VisitCount', 'InCount', 'OutCount', 'DayInCount', 'DayOutCount', 'NightInCount', 'NightOutCount']].sum().copy()
            df_item = df_item.merge(
                last_df, on='CPH', how='left'
            )
            cph_date_df_month = cph_date_df.groupby(['CPH'], as_index=False).agg(
                InOutDays=('InOutDays', lambda x: sum(x))
            )
        df_item['StayText'] = df_item['StayTime'].apply(format_minutes_chinese)
        df_item = df_item.merge(
            address_df_origin[['HomeAddress', 'IsTenant']], on='HomeAddress', how='left'
        )
        df_item = df_item.merge(
            cph_date_df_month, on='CPH', how='left'
        )
        # mask = (df_item['IsTenant'] == False) & (df_item['HomeAddress'].str.strip() == '')
        # df_item.loc[mask, 'IsTenant'] = None
        df_item_mask = (
                df_item['HomeAddress'].fillna('').str.strip().ne('') &
                df_item['HomeAddress'].ne('0-0-0') &
                df_item['IsTenant'].isna()
        )
        df_item.loc[df_item_mask, 'IsTenant'] = False
        df_item['IsTenant'] = df_item['IsTenant'].map({True: '租客', False: '业主'})
        df_item['IsTenant'] = df_item['IsTenant'].fillna('未绑定')
        df_item = df_item.rename(columns={
            'IsTenant': 'ResidentType'
        })
        df_item['HasCoupon'] = df_item['HomeAddress'].isin(coupon_df['HomeAddress'])
        df_item['HasCoupon'] = df_item['HasCoupon'].map({True: '是', False: '否'})
        if order:
            df_item = df_item.sort_values(by=[order], ascending=False).reset_index(drop=True)
        df_item = df_item.drop(columns=['StayTime'])
        df_name_arr.append({
            "name": item,
            "df": df_item
        })
    if return_type == 'json':
        result = {}
        for item in df_name_arr:
            result[item['name']] = df_to_dict(item['df'])
        return result
    else:
        with pd.ExcelWriter(output_path) as writer:
            for item in df_name_arr:
                export_to_excel(item['df'], writer, sheet_name=item['name'])
        return output_path

def cph_compare_data(df, user_df, address_df_origin, coupon_df, mstart, mend, cstart, cend, return_type='json'):
    timestamp = get_timestamp_text(mstart, mend, cstart, cend)
    df_path = os.path.join(_data_dir, f"cache.{timestamp}.cph.pkl")
    output_path = os.path.join(_data_dir, f"{timestamp}.cph.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    if os.path.exists(df_path):
        df = pickle.load(open(df_path, "rb"))
    else:
        main_df = df
        compare_df = df
        if mstart:
            main_df = main_df[main_df['InTime'] >= pd.to_datetime(mstart)]
        if mend:
            main_df = main_df[main_df['OutTime'] <= pd.to_datetime(mend)]
        idx = main_df.groupby('CPH')['OutTime'].idxmax()
        last_main_df = main_df.loc[idx]
        last_main_df = last_main_df[['CPH', 'OutTime']]
        last_main_df['LastInOutTime'] = last_main_df['OutTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        last_main_df = last_main_df.drop(columns=['OutTime'])
        main_date_df = main_df[['CPH', 'Date']].drop_duplicates(subset=['CPH', 'Date'])
        main_date_df = main_date_df.groupby(['CPH'], as_index=False).agg(
            InOutDays=('CPH', lambda x: len(x))
        )
        if cstart:
            compare_df = compare_df[compare_df['InTime'] >= pd.to_datetime(cstart)]
        if cend:
            compare_df = compare_df[compare_df['OutTime'] <= pd.to_datetime(cend)]
        idx = compare_df.groupby('CPH')['OutTime'].idxmax()
        last_compare_df = compare_df.loc[idx]
        last_compare_df = last_compare_df[['CPH', 'OutTime']]
        last_compare_df['LastInOutTime'] = last_compare_df['OutTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        last_compare_df = last_compare_df.drop(columns=['OutTime'])
        compare_date_df = compare_df[['CPH', 'Date']].drop_duplicates(subset=['CPH', 'Date'])
        compare_date_df = compare_date_df.groupby(['CPH'], as_index=False).agg(
            InOutDays=('CPH', lambda x: len(x))
        )

        # 找出各自独有的 CPH
        main_only = main_df[~main_df['CPH'].isin(compare_df['CPH'])]
        main_only = main_only.groupby(['CPH'], as_index=False).agg(
            TypeClass=('TypeClass', first_of_list),
            StayTime=('StayTime', lambda x: sum(x)),
            VisitCount=('CPH', lambda x: len(x)),
            InOutCount=('IsInOut', calc_true_len),
            InCount=('IsOnlyIn', calc_true_len),
            OutCount=('IsOnlyOut', calc_true_len),
            DayInCount=('IsDayIn', calc_true_len),
            DayOutCount=('IsDayOut', calc_true_len)
        )
        main_only = main_only.merge(
            last_main_df, on='CPH', how='left'
        )
        main_only = main_only.merge(
            main_date_df, on='CPH', how='left'
        )
        main_only['CompareType'] = '未出现'

        compare_only = compare_df[~compare_df['CPH'].isin(main_df['CPH'])]
        compare_only = compare_only.groupby(['CPH'], as_index=False).agg(
            TypeClass=('TypeClass', first_of_list),
            StayTime=('StayTime', lambda x: sum(x)),
            VisitCount=('CPH', lambda x: len(x)),
            InOutCount=('IsInOut', calc_true_len),
            InCount=('IsOnlyIn', calc_true_len),
            OutCount=('IsOnlyOut', calc_true_len),
            DayInCount=('IsDayIn', calc_true_len),
            DayOutCount=('IsDayOut', calc_true_len)
        )
        compare_only = compare_only.merge(
            last_compare_df, on='CPH', how='left'
        )
        compare_only = compare_only.merge(
            compare_date_df, on='CPH', how='left'
        )
        compare_only['CompareType'] = '新出现'

        # 合并成新的结果
        df = pd.concat([main_only, compare_only], ignore_index=True)

        df['InCount'] = df['InCount'] + df['InOutCount']
        df['OutCount'] = df['OutCount'] + df['InOutCount']
        df['NightInCount'] = df['InCount'] - df['DayInCount']
        df['NightOutCount'] = df['OutCount'] - df['DayOutCount']
        df = df.drop(columns=['InOutCount'])
        address_df = user_df[['CPH', 'HomeAddress']].sort_values(by=['HomeAddress'], ascending=False).reset_index(drop=True)
        address_df = address_df.groupby('CPH', as_index=False).agg(
            HomeAddress=('HomeAddress', first_of_list)
        )
        user_df = user_df[['HomeAddress', 'UserName']].sort_values(by=['UserName'], ascending=False).reset_index(drop=True)
        user_df = user_df.groupby('HomeAddress', as_index=False).agg(
            UserName=('UserName', first_of_list)
        )
        # --- Step 5. 匹配 HomeAddress ---
        df = df.merge(
            address_df, on='CPH', how='left'
        )
        df = df.merge(
            user_df, on='HomeAddress', how='left'
        )
        df['HomeAddress'] = df['HomeAddress'].fillna('')
        df['UserName'] = df['UserName'].fillna('')
        df['TypeClass'] = df['TypeClass'].fillna('')
        df.loc[df['HomeAddress'] == '0-0-0', 'HomeAddress'] = ''

        df['StayText'] = df['StayTime'].apply(format_minutes_chinese)
        df = df.merge(
            address_df_origin[['HomeAddress', 'IsTenant']], on='HomeAddress', how='left'
        )
        df_item_mask = (
                df['HomeAddress'].fillna('').str.strip().ne('') &
                df['HomeAddress'].ne('0-0-0') &
                df['IsTenant'].isna()
        )
        df.loc[df_item_mask, 'IsTenant'] = False
        df['IsTenant'] = df['IsTenant'].map({True: '租客', False: '业主'})
        df['IsTenant'] = df['IsTenant'].fillna('未绑定')
        df = df.rename(columns={
            'IsTenant': 'ResidentType'
        })
        df['HasCoupon'] = df['HomeAddress'].isin(coupon_df['HomeAddress'])
        df['HasCoupon'] = df['HasCoupon'].map({True: '是', False: '否'})
        df = df[
            ['CPH', 'TypeClass', 'HomeAddress', 'UserName', 'VisitCount', 'InCount', 'OutCount',
             'DayInCount', 'DayOutCount', 'NightInCount', 'NightOutCount', 'StayText', 'LastInOutTime',
             'ResidentType', 'InOutDays', 'HasCoupon', 'CompareType']]
        df.to_pickle(df_path)

    if return_type == 'json':
        return df_to_dict(df)
    else:
        with pd.ExcelWriter(output_path) as writer:
            export_to_excel(df, writer, sheet_name="数据对比结果")
        return output_path


def behavior_data(df, user_df, start, end, return_type='json'):
    timestamp = get_timestamp_text(start, end)
    output_path = os.path.join(_data_dir, f"cache.{timestamp}.behavior.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    pkl_path = os.path.join(_data_dir, f"cache.{timestamp}.behavior.pkl")
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

def compute_income(df, user_df, start, end, return_type='json'):
    timestamp = get_timestamp_text(start, end)
    output_path = os.path.join(_data_dir, f"cache.{timestamp}.income.xlsx")
    if return_type == 'excel' and os.path.exists(output_path):
        return output_path
    pkl_path = os.path.join(_data_dir, f"cache.{timestamp}.income.pkl")
    pkl_m_path = os.path.join(_data_dir, f"cache.{timestamp}.income.month.pkl")
    pkl_f_path = os.path.join(_data_dir, f"cache.{timestamp}.income.family.pkl")
    pkl_t_path = os.path.join(_data_dir, f"cache.{timestamp}.income.tmp.pkl")
    if os.path.exists(pkl_path) and os.path.exists(pkl_m_path) and os.path.exists(pkl_f_path) and os.path.exists(pkl_t_path):
        income_df = pickle.load(open(pkl_path, "rb"))
        income_month_df = pickle.load(open(pkl_m_path, "rb"))
        income_family_df = pickle.load(open(pkl_f_path, "rb"))
        income_tmp_df = pickle.load(open(pkl_t_path, "rb"))
    else:
        income_df = compute_monthly_income(df, user_df)
        income_month_df, income_family_df, income_tmp_df = compute_single_income(df, user_df)
        income_df.to_pickle(pkl_path)
        income_month_df.to_pickle(pkl_m_path)
        income_family_df.to_pickle(pkl_m_path)
        income_tmp_df.to_pickle(pkl_t_path)
    if return_type == 'json':
        detail_df = pd.concat([income_month_df, income_family_df, income_tmp_df], axis=0).groupby(['CPH'])['Fee'].sum().reset_index().merge(user_df[['CPH', 'UserName', 'HomeAddress']], on='CPH', how='left')
        detail_df['UserName'] = detail_df['UserName'].fillna("")
        detail_df['HomeAddress'] = detail_df['HomeAddress'].fillna("")
        return {
            '月度收入': df_to_dict(income_df[['YearMonth', 'Fee']].groupby(['YearMonth'])['Fee'].sum().reset_index().sort_values(by='YearMonth', ascending=False)),
            '年度收入': df_to_dict(income_df.groupby(['Year'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False)),
            '月租车月度收入': df_to_dict(income_df[income_df['TypeClass'] == '月租车'][['YearMonth', 'Fee']].sort_values(by='YearMonth', ascending=False)),
            '亲情车月度收入': df_to_dict(income_df[income_df['TypeClass'] == '亲情车'][['YearMonth', 'Fee']].sort_values(by='YearMonth', ascending=False)),
            '临时车月度收入': df_to_dict(income_df[income_df['TypeClass'] == '临时车'][['YearMonth', 'Fee']].sort_values(by='YearMonth', ascending=False)),
            '月租车年度收入': df_to_dict(income_df[income_df['TypeClass'] == '月租车'].groupby(['Year'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False)),
            '亲情车年度收入': df_to_dict(income_df[income_df['TypeClass'] == '亲情车'].groupby(['Year'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False)),
            '临时车年度收入': df_to_dict(income_df[income_df['TypeClass'] == '临时车'].groupby(['Year'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False)),
            '月租车月度收入明细': df_to_dict(income_month_df[['YearMonth', 'CPH', 'Fee']].sort_values(by='YearMonth', ascending=False)),
            '亲情车月度收入明细': df_to_dict(income_family_df[['YearMonth', 'CPH', 'Fee']].sort_values(by='YearMonth', ascending=False)),
            '临时车月度收入明细': df_to_dict(income_tmp_df[['YearMonth', 'CPH', 'Fee']].sort_values(by='YearMonth', ascending=False)),
            '月租车年度收入明细': df_to_dict(income_month_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False)),
            '亲情车年度收入明细': df_to_dict(income_family_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False)),
            '临时车年度收入明细': df_to_dict(income_tmp_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False)),
            '收入明细': df_to_dict(detail_df.sort_values(by='Fee', ascending=False))
        }
    with pd.ExcelWriter(output_path) as writer:
        export_to_excel(income_df[['YearMonth', 'Fee']].groupby(['YearMonth'])['Fee'].sum().reset_index().sort_values(by='YearMonth', ascending=False), writer, sheet_name="月度收入")
        export_to_excel(income_df.groupby(['Year'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False), writer, sheet_name="年度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '月租车'][['YearMonth', 'Fee']].sort_values(by='YearMonth', ascending=False), writer, sheet_name="月租车月度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '亲情车'][['YearMonth', 'Fee']].sort_values(by='YearMonth', ascending=False), writer, sheet_name="亲情车月度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '临时车'][['YearMonth', 'Fee']].sort_values(by='YearMonth', ascending=False), writer, sheet_name="临时车月度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '月租车'].groupby(['Year'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False), writer, sheet_name="月租车年度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '亲情车'].groupby(['Year'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False), writer, sheet_name="亲情车年度收入")
        export_to_excel(income_df[income_df['TypeClass'] == '临时车'].groupby(['Year'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False), writer, sheet_name="临时车年度收入")

        export_to_excel(income_month_df[['YearMonth', 'CPH', 'Fee']], writer, sheet_name="月租车月度收入明细")
        export_to_excel(income_family_df[['YearMonth', 'CPH', 'Fee']], writer, sheet_name="亲情车月度收入明细")
        export_to_excel(income_tmp_df[['YearMonth', 'CPH', 'Fee']], writer, sheet_name="临时车月度收入明细")
        export_to_excel(income_month_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False), writer, sheet_name="月租车年度收入明细")
        export_to_excel(income_family_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False), writer, sheet_name="亲情车年度收入明细")
        export_to_excel(income_tmp_df.groupby(['Year', 'CPH'])['Fee'].sum().reset_index().sort_values(by='Year', ascending=False), writer, sheet_name="临时车年度收入明细")
        export_to_excel(pd.concat([income_month_df, income_family_df, income_tmp_df], axis=0)
                        .groupby(['CPH'])['Fee'].sum().reset_index()
                        .merge(user_df[['CPH', 'UserName', 'HomeAddress']], on='CPH', how='left')
                        .sort_values(by='Fee', ascending=False),
                        writer, sheet_name="收入明细")
    return output_path

# def user_data():
#     print("读取数据中...")
#     df = load_user_info()
#     print(f"原始记录数: {len(df)}")
#     print("清洗数据中...")
#     df = clean_user_data(df)
#     print(df.head())