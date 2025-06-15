from server.server import app

if __name__ == "__main__":
    app.logger.setLevel('INFO')
    app.run(host='0.0.0.0', port=8080, debug=False)
    # _df, _user_df = get_data()

    # compute_income(_df.copy(), _user_df)
    # behavior_data(_df.copy(), _user_df)
    # area_data(_df.copy(), _user_df)
    # d = analyze_user(_df, _user_df, '20-1-502')

    # print(json.dumps(d, indent=4, ensure_ascii=False))
    # print(pretty_compare_output(d))
    # print("完成")
