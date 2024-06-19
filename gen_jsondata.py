import datetime
import json
import random
import time

### トークン使用量集計プログラムの検証用に使用するサンプルデータの生成プログラム ###

# 出力ファイル名
output_filename = "format_data.json"

# 時間間隔（分単位）
time_interval = 1

# 時間間隔あたりに作成するデータ数
data_per_interval = 2

# 日付範囲
start_date = datetime.datetime(2024, 6, 1, 0, 0, 0)
end_date = datetime.datetime(2024, 7, 1, 0, 0, 0)

# アプリIDリスト
app_id_list = ["kobayashi_com", "yamaguchi_jp", "saito_com"]

# モデルリスト
model_list = ["gpt35", "gpt4"]

# prompt_tokens範囲
prompt_tokens_min = 1
prompt_tokens_max = 100

# completion_tokens範囲
completion_tokens_min = 1
completion_tokens_max = 10

# フォーマット
format_template = {
    "date_time": "",
    "app_id": "",
    "ai_response": {
        "model": "",
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
    }
}

# データリスト
data_list = []

# ループ開始時間
current_time = start_date

# データ生成ループ
while current_time <= end_date:
    # データ生成回数を計算
    data_count = 0
    while data_count < data_per_interval:
        # データ生成
        data = format_template.copy()

        # 日付時刻
        data["date_time"] = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # アプリID
        app_id = random.choice(app_id_list)
        data["app_id"] = app_id

        # モデル
        model = random.choice(model_list)
        data["ai_response"] = {
            "model": model,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0
            }
        }

        # prompt_tokens
        prompt_tokens = random.randint(prompt_tokens_min, prompt_tokens_max)
        data["ai_response"]["usage"]["prompt_tokens"] = prompt_tokens

        # completion_tokens
        completion_tokens = random.randint(completion_tokens_min, completion_tokens_max)
        data["ai_response"]["usage"]["completion_tokens"] = completion_tokens

        # データリストに追加
        data_list.append(data)

        # データ生成回数をカウントアップ
        data_count += 1

    # 次の時間へ
    current_time += datetime.timedelta(minutes=time_interval)

# データをJSON形式でファイルに出力
with open(output_filename, "w") as f:
    json.dump(data_list, f, indent=4)
