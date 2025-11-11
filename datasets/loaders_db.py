import os
import pickle

import pandas as pd
from config.db_config import get_engine, get_config

config = get_config()
data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")

def load_parking_records():
    df_path = os.path.join(data_dir, "MYCARGOOUTRECORD.pkl")
    try:
        if os.path.exists(df_path):
            return pickle.load(open(df_path, "rb"))
    except:
        pass
    if not config['db']:
        return pd.DataFrame()
    query = "SELECT CardType,CPH,InTime,OutTime,InGateName,OutGateName FROM dbo.MYCARGOOUTRECORD"
    try:
        df = pd.read_sql(query, get_engine(), parse_dates=["InTime", "OutTime"])
        df.to_pickle(df_path)
        return df
    except:
        return pd.DataFrame()

def load_user_info():
    df_path = os.path.join(data_dir, "MYJIBENZILIAO.pkl")
    try:
        if os.path.exists(df_path):
            return pickle.load(open(df_path, "rb"))
    except:
        pass
    if not config['db']:
        return pd.DataFrame()
    query = "SELECT UserName+'_'+HomeAddress as UserName,CPH FROM dbo.MYJIBENZILIAO group by UserName,HomeAddress,CPH"
    try:
        user_df = pd.read_sql(query, get_engine())
        user_df.to_pickle(df_path)
        return user_df
    except:
        return pd.DataFrame()
