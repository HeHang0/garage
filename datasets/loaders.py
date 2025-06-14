import pandas as pd
from config.db_config import get_engine

def load_parking_records():
    query = "SELECT CardType,CPH,InTime,OutTime,InGateName,OutGateName FROM dbo.MYCARGOOUTRECORD"
    return pd.read_sql(query, get_engine(), parse_dates=["InTime", "OutTime"])

def load_user_info():
    query = "SELECT UserName+'_'+HomeAddress as UserName,CPH FROM dbo.MYJIBENZILIAO group by UserName,HomeAddress,CPH"
    return pd.read_sql(query, get_engine())
