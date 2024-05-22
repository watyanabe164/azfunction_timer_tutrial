from azure.cosmos import CosmosClient
from datetime import datetime, timedelta
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

    def get_token_usages_group_by_appid(self, fetch_size: int)-> list:
        start_datetime = datetime.strptime(f"2024-04-27 +09:00", "%Y-%m-%d %z")
        end_datetime = datetime.strptime(f"2024-04-29 +09:00", "%Y-%m-%d %z")

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

        return raw_data_list

        """
        totaling_data = {}
        for i, raw_data in enumerate(raw_data_list):
            _id = raw_data["id"]
            _sku = raw_data["sku"]
            totaling_data.update(
                {
                    _id: {
                        _sku: "ok"
                    }
                },
            )                        
        return totaling_data
        """

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
                    c.AppKey,
                    c.AppName,
                    c.AppId
                from
                    chat_history as c
                where
                    c.AppKey != null
                """
        )

        return raw_data_list
