import logging
import os
import time
import requests
import azure.functions as func
from datetime import datetime, timedelta
from correct_token_usage import TotalingTokenUsage, ClientsInfo

app = func.FunctionApp()

@app.schedule(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:

    try:
        ### メイン処理 ###
        cosmos_url = os.getenv("COSMOS_URL")        # CosmosDB URL
        cosmos_key = os.getenv("COSMOS_KEY")        # CosmosDB キー
        mackerel_key = os.getenv("MACKEREL_KEY")    # Mackerel APIキー
        current_time = time.time() # 取得時刻
        metric_time = int(current_time)  # Mackere投稿時の時刻
        
        # Create to_datetime from current_time
        to_datetime = datetime.fromtimestamp(current_time)

        # Calculate 5 minutes before to_datetime
        time_delta = timedelta(minutes=5)
        from_datetime = to_datetime - time_delta

        fetch_size = 100

        usage_client = TotalingTokenUsage(cosmos_url, cosmos_key, "mediator", "chat_history")

        results = usage_client.get_token_usages_group_by_appid(from_datetime, to_datetime, fetch_size)

        clients_info = ClientsInfo(cosmos_url, cosmos_key, "mediator", "clients")
        app_id_division_map = clients_info.get_clients_info(fetch_size)

        request_data = []
        for app_id, usage_by_models in results.items():
            for model, usage in usage_by_models.items():
                token_usage = usage_client.calc_token_usage_for_csv(model, usage["completion_tokens"], usage["prompt_tokens"])
                if token_usage:
                    request_data.append({
                        "name": f"dev_monthly_usage.{app_id_division_map.get(app_id, 'UNDEFINED')}_{app_id}_{model}",
                        "time": metric_time,
                        "value": float(token_usage[-1])
                    })

        logging.info("request_data is ......................................")
        logging.info(request_data)

        headers = {"X-Api-Key": mackerel_key, "Content-Type": "application/json"}
        response = requests.post(
            "https://api.mackerelio.com/api/v0/services/nabe_sv/tsdb",
            json=request_data,
            headers=headers,
        )
        logging.info(f"response is ......................................{response}")


    except Exception as e:
        logging.exception("token集計中にエラーが発生しました")
        raise RuntimeError from e
    
    logging.info('Python timer trigger function executed.')