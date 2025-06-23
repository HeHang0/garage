import json
from itertools import combinations
from math import isnan


def analyze_user(df_io, df_info, text):
    cph_list = df_info[(df_info['HomeAddress'] == text) | (df_info['UserName'] == text)]['CPH'].dropna().unique().tolist()
    return compare_multiple_vehicles(df_io, df_info, cph_list)

def analyze_single_vehicle(df_io, df_info, cph):
    cph = cph.strip() if cph else ''
    df_car = df_io[df_io['CPH'] == cph].copy()
    if df_car.empty:
        return {}
    df_car.sort_values(by='InTime', inplace=True, ascending=False)

    # 出入频率
    df_car['Date'] = df_car['InTime'].dt.date
    freq = df_car.groupby('Date').size().reset_index(name='DailyCount')

    # 白天/夜间统计
    df_car['Hour'] = df_car['InTime'].dt.hour
    df_car['Period'] = df_car['Hour'].apply(lambda h: '白天' if 7 <= h <= 19 else '夜间')
    period_stats = df_car['Period'].value_counts().to_dict()

    # 停车时长
    max_duration = df_car['StayHour'].max()
    avg_duration = round(df_car[df_car['StayHour'] > 1]['StayHour'].mean(), 1)
    max_duration = max_duration if max_duration and not isnan(max_duration) else 0
    avg_duration = avg_duration if avg_duration and not isnan(avg_duration) else 0
    # 出入口偏好
    in_gates = df_car[
        df_car['InGateName'].notnull() &
        df_car['InGateName'].astype(str).str.strip().ne('') &
        ~df_car['InGateName'].astype(str).str.startswith('无')
    ]['InGateName'].value_counts().head(3)
    out_gates = df_car[
        df_car['OutGateName'].notnull() &
        df_car['OutGateName'].astype(str).str.strip().ne('') &
        ~df_car['OutGateName'].astype(str).str.startswith('无')
    ]['OutGateName'].value_counts().head(3)

    # 关联资料
    df_info_car = df_info[df_info['CPH'] == cph].drop_duplicates().to_dict(orient='records')
    df_info_car = df_info_car[0] if df_info_car else None
    return {
        '车牌': cph,
        '车类型': df_car['TypeClass'].iloc[0] if not df_car.empty else '',
        '出入天数': freq.shape[0],
        '总出入记录数': len(df_car),
        '白天/夜间分布': period_stats,
        '最长停留（小时）': max_duration,
        '平均停留（小时）': avg_duration,
        '常用进入位置': json.dumps(in_gates.to_dict(), ensure_ascii=False),
        '常用离开位置': json.dumps(out_gates.to_dict(), ensure_ascii=False),
        '住户信息': f"{df_info_car['HomeAddress']}, {df_info_car['UserName']}" if df_info_car else ''
    }

def compare_multiple_vehicles(df_io, df_info, cph_list):
    results = {}
    for cph in cph_list:
        results[cph] = analyze_single_vehicle(df_io, df_info, cph)

    # 地址分析
    addr_map = {
        cph: df_info[df_info['CPH'] == cph]['HomeAddress'].dropna().unique().tolist()
        for cph in cph_list
    }

    # 交集分析
    date_map = {
        cph: set(df_io[df_io['CPH'] == cph]['InTime'].dt.date) for cph in cph_list
    }
    # print("哈哈哈哈", date_map)
    # overlap_summary = {}
    # for i in range(len(cph_list)):
    #     for j in range(i + 1, len(cph_list)):
    #         c1, c2 = cph_list[i], cph_list[j]
    #         common_dates = date_map[c1] & date_map[c2]
    #         same_home = any(a in addr_map[c2] for a in addr_map[c1])
    #         overlap_summary[f"{c1} 与 {c2}"] = {
    #             '是否同住户': same_home,
    #             '共同出现天数': len(common_dates)
    #         }

    # 多车同时出现分析
    # common_all_dates = set.intersection(*date_map.values()) if date_map else set()
    common_all_dates = compute_common_dates(date_map)
    result:dict[str, dict|object|list] = {
        '车辆分析结果': results,
        # '车辆对比结果': overlap_summary,
        '车辆对比结果': common_all_dates
        # '全部车辆同时出现天数': len(common_all_dates),
        # '全部车辆同时出现日期': json.dumps([d.strftime('%Y-%m-%d') for d in sorted(list(common_all_dates))], ensure_ascii=False),
    }
    # for item in common_all_dates:
    #     result['车辆同时出现结果'][f'{item['count']}辆车同时出现天数'] = len(item['date'])
    #     result['车辆同时出现结果'][f'{item['count']}辆车同时出现车牌'] = json.dumps(item['cph'], ensure_ascii=False)
    #     result['车辆同时出现结果'][f'{item['count']}辆车同时出现日期'] = json.dumps([d.strftime('%Y-%m-%d') for d in sorted(item['date'])], ensure_ascii=False)
    return result

def compute_common_dates(cph_dict):
    result = []

    cph_list = list(cph_dict.keys())

    for r in range(len(cph_list), 1, -1):  # 从多到少
        for cph_combo in combinations(cph_list, r):
            # 取出这些车的日期集合并做交集
            common_dates = set(cph_dict[cph_combo[0]])
            for cph in cph_combo[1:]:
                common_dates &= set(cph_dict[cph])

            if common_dates:
                result.append({
                    "count": r,
                    "cph": list(cph_combo),
                    "date": [d.strftime('%Y-%m-%d') for d in sorted(common_dates)]
                })

    return result

def format_cph_appearance(data):
    from collections import defaultdict

    grouped = defaultdict(list)
    for item in data:
        grouped[item["count"]].append(item)

    lines = []
    for count in sorted(grouped.keys(), reverse=True):
        lines.append("====================================")
        lines.append(f"{count}辆车同时出现：")
        for entry in grouped[count]:
            cphs = entry["cph"]
            dates = entry["date"]
            lines.append(f"\t{cphs}：")
            lines.append(f"\t\t天数：{len(dates)}")
            lines.append(f"\t\t日期：{dates}")
    return "\n".join(lines)

def pretty_compare_output(result: dict):
    # 车辆分析结果汇总表
    text = "📊 每辆车行为分析：\n"
    summary_text = ""
    for cph, detail in result['车辆分析结果'].items():
        summary_text += f"{cph}:\n"
        for key, value in detail.items():
            summary_text += f"\t{key}: {value or ''}\n"
    # 输出车辆汇总
    text += summary_text

    # 输出交集对比
    text += "\n🔍 车辆对比结果：\n"
    # overlap_text = format_cph_appearance(result['车辆对比结果'])+"\n"
    # for k, detail in result['车辆对比结果'].items():
    #     overlap_text += f"{k}:\n"
    #     overlap_text += f"\t是否同住户: {'是' if detail['是否同住户'] else '是'}\n"
    #     overlap_text += f"\t{'共同出现天数'}: {detail['共同出现天数']}\n"
    text +=  format_cph_appearance(result['车辆对比结果'])
    return text