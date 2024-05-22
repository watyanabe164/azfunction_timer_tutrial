import logging
from azure.cosmos import CosmosClient
from datetime import datetime, timedelta
from decimal import ROUND_CEILING, Decimal
import json


class TotalingTokenUsage:
    """Tokenの利用料を取得計算するクラス"""

    def __init__(self, cosmos_url: str, cosmos_key: str, cosmos_db_name: str, cosmos_container_name: str) -> None:
        """コンストラクタ

        Args:
            cosmos_url(str): 接続するCosmosDBのURL
            cosmos_key(str): 接続するCosmosDBのAPI KEY
            cosmos_db_name(str): 接続するCosmosDBのdatabase名
            cosmos_container_name(str): 接続するCosmosDBのcontainer名
        """
        cosmos_client = CosmosClient(cosmos_url, cosmos_key)
        database = cosmos_client.get_database_client(cosmos_db_name)
        self.container = database.get_container_client(cosmos_container_name)

        cosmos_client_csv = CosmosClient(cosmos_url, cosmos_key)
        database_csv = cosmos_client_csv.get_database_client(cosmos_db_name)
        self.container_csv = database_csv.get_container_client(cosmos_container_name)

        self.token_rate_map = {
            "gpt35": {
                "prompt": 0.148,
                "completion": 0.296
            },
            "gpt4": {
                "prompt": 1.48,
                "completion": 2.96
            }
        }

    def get_token_usages_group_by_appid(self, fetch_size: int)-> list:
        start_datetime = datetime.strptime(f"2024-04-01 +09:00", "%Y-%m-%d %z")
        end_datetime = datetime.strptime(f"2024-06-01 +09:00", "%Y-%m-%d %z")

        cosmos_date_format = "%Y-%m-%d %H:%M:%S"
        sd = start_datetime.strftime(cosmos_date_format)
        ed = end_datetime.strftime(cosmos_date_format)
        
        raw_data_list = self.container.query_items(
            enable_cross_partition_query=True,
            max_item_count=fetch_size,
            query="""
                select
                    c.ai_response.model,
                    c.ai_response.usage,
                    c.app_id
                from
                    chat_history as c
                where
                    c.ai_response != null AND
                    c.ai_response.model != null AND
                    c.ai_response.usage != null AND
                    c.date_time >= @start_datetime AND
                    c.date_time < @end_datetime
                """,
            parameters=[
                {"name": "@start_datetime", "value": sd},
                {"name": "@end_datetime", "value": ed},
            ]
        )

        totaling_data = {}
        for i, raw_data in enumerate(raw_data_list):
            _app_id = raw_data["app_id"]
            _model = raw_data["model"]
            _usage = raw_data["usage"]
            if _usage:
                if _app_id in totaling_data:
                    if _model in totaling_data[_app_id]:
                        totaling_data[_app_id][_model]["prompt_tokens"] += _usage["prompt_tokens"]
                        totaling_data[_app_id][_model]["completion_tokens"] += _usage["completion_tokens"]
                    else:
                        totaling_data[_app_id].update({_model: _usage})
                else:
                    totaling_data.update(
                        {
                            _app_id: {
                                _model: _usage,
                            }
                        },
                    )
 
        return totaling_data

    def calc_token_usage_for_csv(self, model_name: str, completion_tokens: int, prompt_tokens: int) -> list:
        """利用したtoken量から料金を計算する

        Args:
            model_name(str): 利用モデル名
            completion_tokens(int): completion_token数
            prompt_tokens(int): prompt_token数

        Returns:
            list: [ model_name, prompt_token数, prompt_token_rate, completion_token数, completion_token_rate ]
        """
        if model_name not in self.token_rate_map:
            return None
        prompt_token_rate = self.token_rate_map[model_name]["prompt"]
        completion_token_rate = self.token_rate_map[model_name]["completion"]
        total_price = (prompt_tokens * prompt_token_rate / 1000) + (completion_tokens * completion_token_rate / 1000)
        # 愚直に計算した値は小数を含むので繰り上げる
        # 繰り上げなのは不足分が出ないようにするため、請求額は多くなるがapplicationあたり1円なので問題ないと判断
        total_price = Decimal(str(total_price)).quantize(Decimal("1"), rounding=ROUND_CEILING)
        return [model_name, prompt_tokens, prompt_token_rate, completion_tokens, completion_token_rate, total_price]


class ClientsInfo:
    """クライアントシステム情報を取得するクラス"""

    def __init__(self, cosmos_url: str, cosmos_key: str, cosmos_db_name: str, cosmos_container_name: str) -> None:
        """コンストラクタ

        Args:
            cosmos_url(str): 接続するCosmosDBのURL
            cosmos_key(str): 接続するCosmosDBのAPI KEY
            cosmos_db_name(str): 接続するCosmosDBのdatabase名
            cosmos_container_name(str): 接続するCosmosDBのcontainer名
        """
        cosmos_client = CosmosClient(cosmos_url, cosmos_key)
        database = cosmos_client.get_database_client(cosmos_db_name)
        self.container = database.get_container_client(cosmos_container_name)

    def get_clients_info(self, fetch_size: int)-> list:
        raw_data_list = self.container.query_items(
            enable_cross_partition_query=True,
            max_item_count=fetch_size,
            query="""
                select
                    c.AppId,
                    c.Division
                from
                    chat_history as c
                where
                    c.AppId != null
                """
        )
        
        app_id_division_map = {row["AppId"]: row["Division"] for row in raw_data_list}

        return app_id_division_map
