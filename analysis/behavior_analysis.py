import pandas as pd


def analyze_activity_patterns(df, user_df):
    df = df[df['CPH'].str.len() > 0].copy()
    df_sorted = df.sort_values(by='InTime', ascending=False)
    df_typeclass = df_sorted.groupby('CPH', as_index=False).first()
    df_typeclass = df_typeclass[['CPH', 'TypeClass']]
    df['HourIn'] = df['InTime'].dt.hour
    df['HourOut'] = df['OutTime'].dt.hour
    freq_df = df.groupby('CPH').size().reset_index(name='VisitCount')

    day_in_mask = df['HourIn'].between(6, 18)
    night_in_mask = ~day_in_mask
    day_out_mask = df['HourIn'].between(6, 18)
    night_out_mask = ~day_out_mask

    day_in_df = df[day_in_mask & (df['IsOnlyIn'] | df['IsInOut'])].groupby('CPH').size().reset_index(name='DayInCount')
    day_out_df = df[day_out_mask & (df['IsOnlyOut'] | df['IsInOut'])].groupby('CPH').size().reset_index(name='DayOutCount')
    night_in_df = df[night_in_mask & (df['IsOnlyIn'] | df['IsInOut'])].groupby('CPH').size().reset_index(name='NightInCount')
    night_out_df = df[night_out_mask & (df['IsOnlyOut'] | df['IsInOut'])].groupby('CPH').size().reset_index(name='NightOutCount')

    stay_days = df.groupby('CPH')['StayDay'].max().reset_index(name='MaxStayDay')

    result = freq_df.merge(day_in_df, on='CPH', how='left')
    result = result.merge(day_out_df, on='CPH', how='left')
    result = result.merge(night_in_df, on='CPH', how='left')
    result = result.merge(night_out_df, on='CPH', how='left')
    result = result.merge(stay_days, on='CPH', how='left')
    result = result.merge(user_df[['CPH', 'UserName', 'HomeAddress']], on='CPH', how='left')
    result = result.merge(df_typeclass, on='CPH', how='left')

    result['DayInCount'] = result['DayInCount'].fillna(0)
    result['DayOutCount'] = result['DayOutCount'].fillna(0)
    result['NightInCount'] = result['NightInCount'].fillna(0)
    result['NightOutCount'] = result['NightOutCount'].fillna(0)
    result['HomeAddress'] = result['HomeAddress'].fillna('')

    return result.sort_values(by='VisitCount', ascending=False)