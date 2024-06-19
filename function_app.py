import logging
import os
import time
import requests
import azure.functions as func
from datetime import datetime, timedelta
from correct_token_usage import TotalingTokenUsage, ClientsInfo

app = func.FunctionApp()

# リアルタイムでトークン使用量を集計
@app.schedule(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False)
def timer_trigger(myTimer: func.TimerRequest) -> None:

    try:
        # 環境変数の読み込み
        env_name = os.getenv("ENV_NAME")
        fetch_size = os.getenv("FETCH_SIZE")
        cosmos_url = os.getenv("COSMOS_URL")
        cosmos_key = os.getenv("COSMOS_KEY")
        mackerel_key = os.getenv("MACKEREL_KEY")

        # 計測実施時刻のセット
        metric_time = int(time.time())

        # 集計期間の定義
        time_intervals = {
            "5min": timedelta(minutes=5),
        }

        # 集計期間ごとに処理を実行
        for interval_name, time_delta in time_intervals.items():
            process_interval_data(metric_time, time_delta, interval_name, env_name, fetch_size, cosmos_url,
                                 cosmos_key, mackerel_key)

    except Exception as e:
        logging.exception("トークン集計中にエラーが発生しました")
        raise RuntimeError from e

    logging.info('Python timer trigger function executed.')

# 日次処理でトークン使用量を集計
@app.timer_trigger(schedule="0 55 23 * * *", arg_name="myTimer", run_on_startup=True,
                  use_monitor=False)
def timer_trigger_daily(myTimer: func.TimerRequest) -> None:

    try:
        # 環境変数の読み込み
        env_name = os.getenv("ENV_NAME")
        fetch_size = os.getenv("FETCH_SIZE")
        cosmos_url = os.getenv("COSMOS_URL")
        cosmos_key = os.getenv("COSMOS_KEY")
        mackerel_key = os.getenv("MACKEREL_KEY")

        # 計測実施時刻のセット
        metric_time = int(time.time())

        # 集計期間の定義
        time_intervals = {
            "1day": timedelta(days=1),
            "1week": timedelta(weeks=1),
            "1month": timedelta(days=30)
        }

        # 集計期間ごとに処理を実行
        for interval_name, time_delta in time_intervals.items():
            process_interval_data(metric_time, time_delta, interval_name, env_name, fetch_size, cosmos_url,cosmos_key, mackerel_key)

    except Exception as e:
        logging.exception("トークン集計中にエラーが発生しました")
        raise RuntimeError from e

    logging.info('Python timer trigger function executed.')



def process_interval_data(metric_time, time_delta, interval_name, env_name, fetch_size, cosmos_url, cosmos_key, mackerel_key):
    # 集計開始日時、集計終了日時の計算
    start_datetime, end_datetime = calculate_interval_dates(metric_time, time_delta, interval_name)

    # 指定した集計期間でのトークン使用量を取得
    logging.info(f"start get_token_usages_group_by_appid for {start_datetime} to {end_datetime} is ......................................")    
    usage_client = TotalingTokenUsage(cosmos_url, cosmos_key, "mediator", "chat_history")
    results = usage_client.get_token_usages_group_by_appid(start_datetime, end_datetime, fetch_size)

    # クライアントシステム一覧情報を取得
    clients_info = ClientsInfo(cosmos_url, cosmos_key, "mediator", "chat_history")
    app_id_division_map = clients_info.get_clients_info(fetch_size)

    logging.info(f"results for {interval_name} is ......................................")
    logging.info(results)

    # クライアントシステム別×モデル別でトークン使用量を集計
    # TODO:元々コスト計算のために作った監視の仕組みのはずなのに、いつの間にかコスト計算の処理をやめてるのは本末転倒な気がする。リアルタイム処理についてはコスト計算はいらないけど日次処理についてはキチンとコスト計算の考えを取り入れるべき
    request_data = []
    for app_id, usage_by_models in results.items():
        for model, usage in usage_by_models.items():
            token_usage = usage_client.calc_token_usage_for_csv(model, usage["completion_tokens"], usage["prompt_tokens"])
            if token_usage:
                request_data.append({
                    "name": f"{env_name}_{interval_name}_usage.{app_id_division_map.get(app_id, 'UNDEFINED')}_{app_id}_{model}",
                    "time": metric_time,
                    "value": float(token_usage[-1])
                })
            else:
                request_data.append({
                    "name": f"{env_name}_{interval_name}_usage.{app_id_division_map.get(app_id, 'UNDEFINED')}_{app_id}_{model}",
                    "time": metric_time,
                    "value": 0
                })

    logging.info(f"request_data for {interval_name} is ......................................")
    logging.info(request_data)

    # 集計結果をMackerelサービスメトリクスAPIで送信
    headers = {"X-Api-Key": mackerel_key, "Content-Type": "application/json"}
    response = requests.post(
        "https://api.mackerelio.com/api/v0/services/nabe_sv/tsdb",
        json=request_data,
        headers=headers,
    )
    logging.info(f"response for {interval_name} is ......................................{response}")


# 集計期間を算出
def calculate_interval_dates(metric_time, time_delta, interval_name):
    current_datetime = datetime.fromtimestamp(metric_time)

    # １日：当日0:00～現在時刻
    if interval_name == "1day":
        start_datetime = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    # １週間：今週月曜日0:00～現在時刻
    elif interval_name == "1week":
        start_datetime = current_datetime - timedelta(days=current_datetime.weekday() + 1)  # Monday
        start_datetime = start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    # １か月：当月１日0:00～現在時刻
    elif interval_name == "1month":
        start_datetime = current_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_datetime = current_datetime - time_delta
    end_datetime = current_datetime
    
    return start_datetime, end_datetime