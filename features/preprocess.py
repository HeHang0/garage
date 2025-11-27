import re

import pandas as pd


def classify_card_type(row, family_cph):
    cph = row['CPH']
    card_type = row['CardType']
    if cph in family_cph:
        return '亲情车'
    if pd.isnull(card_type):
        return '免费车'
    if card_type.startswith('Mth') or card_type.startswith('Mtp'):
        return '月租车'
    elif card_type.startswith('Tmp') or card_type.startswith('Person'):
        return '临时车'
    else:  # Fre / Tfr 等
        return '免费车'

def is_daytime(t):
    if pd.isna(t):
        return False
    hour = t.hour
    return 6 <= hour < 18

def clean_parking_data(df, family_cph):
    df = df.drop_duplicates()
    df['InGateName'] = df['InGateName'].fillna("")
    df['OutGateName'] = df['OutGateName'].fillna("")
    df['StayTime'] = ((df['OutTime'] - df['InTime']).dt.total_seconds() / 60).astype(int)
    df['StayTime'] = df['StayTime'].fillna(0)
    df['StayHour'] = ((df['StayTime']) / 60).round(1)
    df['StayDay'] = ((df['StayTime']) / 1440).round(1)
    df['StayText'] = df['StayTime'].apply(format_minutes_chinese)
    df['TypeClass'] = df.apply(lambda row: classify_card_type(row, family_cph), axis=1)
    df['InLen'] = df['InGateName'].apply(lambda x: len(x) if x and not x.startswith('无') and not x.startswith('未') else 0)
    df['OutLen'] = df['OutGateName'].apply(lambda x: len(x) if x and not x.startswith('无') and not x.startswith('未') else 0)
    df['IsOnlyIn'] = (df['InLen'] > 0) & (df['OutLen'] <= 0)
    df['IsOnlyOut'] = (df['OutLen'] > 0) & (df['InLen'] <= 0)
    df['IsInOut'] = (~df['IsOnlyIn']) & (~df['IsOnlyOut'])
    df['HourIn'] = df['InTime'].dt.hour
    df['HourOut'] = df['OutTime'].dt.hour
    df['IsDayIn'] = df['HourIn'].between(6, 18)
    df['IsDayOut'] = df['HourOut'].between(6, 18)
    df['IsDayIn'] = df['IsDayIn'] & (df['IsOnlyIn'] | df['IsDayOut'])
    df['IsDayOut'] = df['IsDayOut'] & (df['IsOnlyOut'] | df['IsDayOut'])
    df['YearMonth'] = df['InTime'].dt.to_period('M').astype(str)
    df['Date'] = df['InTime'].dt.strftime('%Y-%m-%d')
    df['Year'] = df['InTime'].dt.year
    df['Month'] = df['InTime'].dt.month
    df = df.sort_values(by='InTime', ascending=False).reset_index(drop=True)
    return df.drop(columns=['InLen', 'OutLen'])

pattern_address = r'[\d]+[\-]+[\d]+[\-]*[\d]*'
def classify_home_address(user_name):
    if pd.isnull(user_name) or len(user_name) == 0:
        return ''
    match = re.search(pattern_address, user_name)

    if match:
        return match.group()
    else:
        return ''

pattern_user = r'[\d\-_幢]+'
def classify_user_name(user_name):
    if pd.isnull(user_name) or len(user_name) == 0:
        return ''
    return re.sub(pattern_user, '', user_name)


def clean_user_data(df):
    df['HomeAddress'] = df['UserName'].apply(classify_home_address)
    df['UserName'] = df['UserName'].apply(classify_user_name).fillna("")
    df = df.drop_duplicates()
    df = df.groupby(['HomeAddress', 'CPH'])['UserName'].agg(lambda x: ''.join(x)).reset_index()
    df['Order'] = df.groupby('HomeAddress').cumcount() + 1
    df.loc[df['HomeAddress'].str.strip() == '', 'Order'] = 1
    df['UserName'] = df['UserName'].fillna("")
    df['HomeAddress'] = df['HomeAddress'].fillna("")
    return df

def format_minutes_chinese(minutes):
    minutes = int(minutes)
    if minutes <= 0:
        return ""
    if minutes < 60:
        return f"{minutes}分"
    elif minutes < 1440:  # 小于一天
        h, m = divmod(minutes, 60)
        parts = []
        if h:
            parts.append(f"{h}小时")
        if m:
            parts.append(f"{m}分")
        return ''.join(parts)
    else:
        d, rem = divmod(minutes, 1440)
        h, m = divmod(rem, 60)
        parts = []
        if d:
            parts.append(f"{d}天")
        if h:
            parts.append(f"{h}小时")
        if m:
            parts.append(f"{m}分")
        return ''.join(parts)