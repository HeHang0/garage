import re

import pandas as pd


def classify_card_type(card_type):
    if pd.isnull(card_type):
        return '免费车'
    if card_type.startswith('Mth') or card_type.startswith('Mtp'):
        return '月租车'
    elif card_type.startswith('Tmp') or card_type.startswith('Person'):
        return '临时车'
    else:#if card_type.startswith('Fre') or card_type.startswith('Tfr'):
        return '免费车'

def clean_parking_data(df):
    df = df.drop_duplicates()
    df['StayTime'] = ((df['OutTime'] - df['InTime']).dt.total_seconds() / 60).astype(int)
    df['StayHour'] = ((df['StayTime']) / 60).round(1)
    df['StayDay'] = ((df['StayTime']) / 1440).round(1)
    df['TypeClass'] = df['CardType'].apply(classify_card_type)
    df['InLen'] = df['InGateName'].apply(lambda x: len(x) if x and not x.startswith('无') else 0)
    df['OutLen'] = df['OutGateName'].apply(lambda x: len(x) if x and not x.startswith('无') else 0)
    df['IsOnlyIn'] = (df['InLen'] > 0) & (df['OutLen'] <= 0)
    df['IsOnlyOut'] = (df['OutLen'] > 0) & (df['InLen'] <= 0)
    df['IsInOut'] = (~df['IsOnlyIn']) & (~df['IsOnlyOut'])
    df['HourIn'] = df['InTime'].dt.hour
    df['HourOut'] = df['OutTime'].dt.hour
    df['YearMonth'] = df['InTime'].dt.to_period('M')
    df['Year'] = df['InTime'].dt.year
    df['Month'] = df['InTime'].dt.month
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
    return df