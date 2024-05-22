import logging
import os
import time
import requests
import azure.functions as func
from datetime import datetime, timedelta
from correct_token_usage import TotalingTokenUsage, ClientsInfo

app = func.FunctionApp()

@app.schedule(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    try:
        ### メイン処理 ###
        cosmos_url = os.getenv("COSMOS_URL")        # CosmosDB URL
        cosmos_key = os.getenv("COSMOS_KEY")        # CosmosDB キー
        mackerel_key = os.getenv("MACKEREL_KEY")    # Mackerel APIキー
        metric_time = int(time.time())  # 取得時刻

        logging.info(f"cosmos_url variable value: {cosmos_url}")
        logging.info(f"cosmos_key variable value: {cosmos_key}")

        fetch_size = 100

        usage_client = TotalingTokenUsage(cosmos_url, cosmos_key, "mediator", "chat_history")
        results = usage_client.get_token_usages_group_by_appid(fetch_size)

        clients_info = ClientsInfo(cosmos_url, cosmos_key, "mediator", "chat_history")
        app_id_division_map = clients_info.get_clients_info(fetch_size)

        request_data = []
        for app_id, usage_by_models in results.items():
            for model, usage in usage_by_models.items():
                token_usage = usage_client.calc_token_usage_for_csv(model, usage["completion_tokens"], usage["prompt_tokens"])
                if token_usage:
                    request_data.append({
                        "name": f"dev_monthly_usage.{app_id_division_map.get(app_id, 'UNDEFINED')}_{app_id}_{model}",
                        "time": metric_time,
                        "value": int(token_usage[-1])
                    })

        logging.info("request_data is ......................................")
        logging.info(request_data)

        headers = {"X-Api-Key": mackerel_key, "Content-Type": "application/json"}
        response = requests.post(
            "https://api.mackerelio.com/api/v0/services/nabe_sv/tsdb",
            json=request_data,
            headers=headers,
        )
        logging.info("response is ......................................{response}")


    except Exception as e:
        logging.exception("token集計中にエラーが発生しました")
        raise RuntimeError from e
    
    logging.info('Python timer trigger function executed.')