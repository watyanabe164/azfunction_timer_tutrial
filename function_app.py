import logging
import os
import azure.functions as func
import sys
from datetime import datetime, timedelta
from correct_token_usage import TotalingTokenUsage, ClientsInfo

app = func.FunctionApp()

@app.schedule(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    my_variable = os.getenv("FUNCTIONS_WORKER_RUNTIME")
    logging.info(f"My environment variable value: {my_variable}")

    try:
        ### メイン処理 ###
        cosmos_url = os.getenv("COSMOS_URL")
        ## nbdb151vのキー情報をポータルから確認して入力してね
        cosmos_key = os.getenv("COSMOS_KEY")

        logging.info(f"cosmos_url variable value: {cosmos_url}")
        logging.info(f"cosmos_key variable value: {cosmos_key}")

        fetch_size = 100

        usage_client = TotalingTokenUsage(cosmos_url, cosmos_key, "mediator", "chat_history")
        usage_results = usage_client.get_token_usages_group_by_appid(fetch_size)
        logging.info(list(usage_results))

        clients_info = ClientsInfo(cosmos_url, cosmos_key, "mediator", "chat_history")
        clients_results = clients_info.get_clients_info(fetch_size)
        logging.info(list(clients_results))
    except Exception as e:
        logging.exception("token集計中にエラーが発生しました")
        raise RuntimeError from e
    
    logging.info('Python timer trigger function executed.')

