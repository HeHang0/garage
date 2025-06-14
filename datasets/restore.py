import pandas as pd


def restore_run_from_excel(excel_file, sheet_name='Sheet1'):
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

def restore_user_from_excel(excel_file, sheet_name='Sheet1'):
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