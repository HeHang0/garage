import json
import os

from flask import Flask, jsonify, request, Response, send_file, send_from_directory
from flask_cors import CORS
import gzip

from analysis.access_analysis import analyze_user, pretty_compare_output, analyze_single_vehicle, \
    compare_multiple_vehicles
from server.data import area_data, get_data, behavior_data, compute_income, record_data, user_data, cph_data, \
    cph_compare_data

_cur_dir = os.path.dirname(os.path.abspath(__file__))
_front_dir = os.path.join(_cur_dir, '../frontend')

app = Flask(__name__, static_folder=_front_dir, static_url_path='')
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://hk.picapico.top"])

_df, _user_df, _address_df, _coupon_df = get_data()

def api_response(data="", message="success", status=200):
    data = json.dumps({
        "status": status,
        "message": message,
        "data": data
    }, ensure_ascii=False)
    return Response(gzip.compress(data.encode('utf-8')),
                    content_type='application/json; charset=utf-8',
                    headers={'Content-Encoding': 'gzip'})

# 所有非 /api 路由，走前端页面分发
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # 默认返回 index.html（SPA 路由）
        return send_from_directory(app.static_folder, 'index.html')

# 各接口返回对应的 DataFrame 内容
@app.route('/api/area', methods=['GET'])
def get_area():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    result = area_data(_df.copy(), _user_df.copy(), start, end)
    return api_response(result)

@app.route('/api/user', methods=['GET'])
def get_user():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    order = request.args.get('order', 'HomeAddress')
    result = user_data(_df.copy(), _user_df.copy(), _address_df.copy(), _coupon_df.copy(), order, start, end)
    return api_response(result)

@app.route('/api/user/excel', methods=['GET'])
def get_user_file():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    order = request.args.get('order', 'HomeAddress')
    output = user_data(_df.copy(), _user_df.copy(), _address_df.copy(), _coupon_df.copy(), order, start, end, 'excel')
    return send_file(
        output,
        as_attachment=True,
        download_name="住户记录.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/api/cphl', methods=['GET'])
def get_cph_list():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    order = request.args.get('order', 'VisitCount')
    result = cph_data(_df.copy(), _user_df.copy(), _address_df.copy(), _coupon_df.copy(), order, start, end)
    return api_response(result)

@app.route('/api/cphl/excel', methods=['GET'])
def get_cph_list_file():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    order = request.args.get('order', 'VisitCount')
    output = cph_data(_df.copy(), _user_df.copy(), _address_df.copy(), _coupon_df.copy(), order, start, end, 'excel')
    return send_file(
        output,
        as_attachment=True,
        download_name="车辆记录.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/api/cphcompare', methods=['GET'])
def get_cph_compare_list():
    mstart = request.args.get('mstart', '')
    mend = request.args.get('mend', '')
    cstart = request.args.get('cstart', '')
    cend = request.args.get('cend', '')
    result = cph_compare_data(_df.copy(), _user_df.copy(), _address_df.copy(), _coupon_df.copy(), mstart, mend, cstart, cend)
    return api_response(result)

@app.route('/api/cphcompare/excel', methods=['GET'])
def get_cph_compare_list_file():
    mstart = request.args.get('mstart', '')
    mend = request.args.get('mend', '')
    cstart = request.args.get('cstart', '')
    cend = request.args.get('cend', '')
    output = cph_compare_data(_df.copy(), _user_df.copy(), _address_df.copy(), _coupon_df.copy(), mstart, mend, cstart, cend, 'excel')
    return send_file(
        output,
        as_attachment=True,
        download_name="车辆对比记录.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/api/record', methods=['GET'])
def get_record():
    name = request.args.get('name', '')
    cph_list = request.args.get('cph', '').strip().replace("，", ",").split(',')
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    date = request.args.get('date', '')
    abnormal = request.args.get('abnormal', '')
    result = record_data(_df.copy(), _user_df.copy(), cph_list, name, start, end, date, abnormal)
    return api_response(result)

@app.route('/api/area/excel', methods=['GET'])
def get_area_file():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    output = area_data(_df.copy(), _user_df.copy(), start, end, 'excel')
    return send_file(
        output,
        as_attachment=True,
        download_name="车牌分析.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/api/behavior', methods=['GET'])
def get_behavior():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    result = behavior_data(_df.copy(), _user_df.copy(), start, end)
    return api_response(result)

@app.route('/api/behavior/excel', methods=['GET'])
def get_behavior_file():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    output = behavior_data(_df.copy(), _user_df.copy(), start, end, 'excel')
    return send_file(
        output,
        as_attachment=True,
        download_name="行为分析.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/api/income', methods=['GET'])
def get_income():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    result = compute_income(_df.copy(), _user_df.copy(), start, end)
    return api_response(result)

@app.route('/api/income/excel', methods=['GET'])
def get_income_file():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    output = compute_income(_df.copy(), _user_df.copy(), start, end, 'excel')
    return send_file(
        output,
        as_attachment=True,
        download_name="收入汇总.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/api/cph', methods=['GET'])
def get_cph():
    cph_list = request.args.get('cph', '').strip().replace("，", ",").split(',')
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    if len(cph_list) < 1:
        return api_response()
    if len(cph_list) == 1:
        d = analyze_single_vehicle(_df.copy(), _user_df.copy(), cph_list[0], start, end)
        summary_text = ""
        for key, value in d.items():
            summary_text += f"{key}: {value or ''}\n"
    else:
        d = compare_multiple_vehicles(_df.copy(), _user_df.copy(), cph_list, start, end)
        summary_text = pretty_compare_output(d)

    return api_response(summary_text)

@app.route('/api/name', methods=['GET'])
def get_name():
    name = request.args.get('name', '')
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    d = analyze_user(_df.copy(), _user_df.copy(), name, start, end)
    return api_response(pretty_compare_output(d))