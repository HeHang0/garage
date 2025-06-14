import re

area_dict = {
    "京": "北京市",
    "津": "天津市",
    "沪": "上海市",
    "渝": "重庆市",
    "宁": "宁夏回族自治区",
    "新": "新疆维吾尔自治区",
    "藏": "西藏自治区",
    "桂": "广西壮族自治区",
    "蒙": "内蒙古自治区",
    "辽": "辽宁省",
    "吉": "吉林省",
    "黑": "黑龙江省",
    "冀": "河北省",
    "晋": "山西省",
    "苏": "江苏省",
    "浙": "浙江省",
    "皖": "安徽省",
    "闽": "福建省",
    "赣": "江西省",
    "鲁": "山东省",
    "豫": "河南省",
    "鄂": "湖北省",
    "湘": "湖南省",
    "琼": "海南省",
    "川": "四川省",
    "贵": "贵州省",
    "云": "云南省",
    "陕": "陕西省",
    "甘": "甘肃省",
    "青": "青海省",
    "粤": "广东省",
    "临": "临时牌"
}

pattern_5 = r'(.)\1\1\1\1'
pattern_4 = r'(.)\1\1\1'
pattern_3 = r'(.)\1\1'
pattern_num = r'[\d]{3,}'

def max_consecutive_digit_count(n):
    digits = [int(d) for d in str(n)]
    max_len = cur_len = 1

    for i in range(1, len(digits)):
        if digits[i] == digits[i-1] + 1:
            cur_len += 1
            max_len = max(max_len, cur_len)
        else:
            cur_len = 1  # 重置计数
    return max_len

def has_three_consecutive_same_or_numbers(cph):
    cph = str(cph)

    # 1. 连续相同字符
    if re.search(pattern_5, cph):
        return 5
    if re.search(pattern_4, cph):
        return 4
    if re.search(pattern_3, cph):
        return 3

    # 2. 连续数字（递增或递减）
    digits_text = re.search(pattern_num, cph)
    if not digits_text:
        return 0
    digits = int(digits_text.group())
    max_len = max_consecutive_digit_count(digits)

    return max_len if max_len >= 4 else 0  # 可选：长度1的不算“连续”

def analyze_area_plate(df, user_df):
    df = df[df['CPH'].str.len() > 0][['CPH']].drop_duplicates()
    special_df = df.groupby('CPH').size().reset_index(name='VisitCount').merge(user_df, on='CPH', how='left')
    special_df['SpecialCPH'] = special_df['CPH'].apply(has_three_consecutive_same_or_numbers)
    special_df['UserName'] = special_df['UserName'].fillna('')
    special_df['HomeAddress'] = special_df['HomeAddress'].fillna('')
    df['Province'] = df['CPH'].str[0].apply(lambda x: area_dict.get(x, "未知"))
    df['CarType'] = df['CPH'].apply(lambda x: '电车' if len(str(x)) == 8 else '油车')

    unknow_cph = df[df['Province'] == '未知'][['CPH']].drop_duplicates()
    province_counts = df.groupby('Province').size().reset_index(name='Count')
    province_counts = province_counts.sort_values(by='Count', ascending=False)
    car_type_counts = df.groupby('CarType').size().reset_index(name='VisitCount')
    car_type_counts.columns = ['CarType', 'Count']
    return province_counts, unknow_cph,car_type_counts,special_df[special_df['SpecialCPH'] >= 3].sort_values(by='SpecialCPH', ascending=False).drop(columns=['Order', 'SpecialCPH'])

def analyze_plate(df):
    car_df = df[df['CPH'] == plate].copy()
    if car_df.empty:
        print("无该车牌记录")
        return

    car_df['InHour'] = car_df['InTime'].dt.hour
    car_df['OutHour'] = car_df['OutTime'].dt.hour
    freq = car_df['YearMonth'].value_counts().sort_index()
    return freq
