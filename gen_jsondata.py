### サンプルデータ作成用プログラム

import datetime
import json
import random
import time

# 出力ファイル名
output_filename = "format_data.json"

# 日付範囲
start_date = datetime.datetime(2024, 5, 21, 0, 0, 0)
end_date = datetime.datetime(2024, 5, 23, 0, 0, 0)

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

# 5分間隔でループ
current_time = start_date
while current_time <= end_date:
    # データ生成
    data = format_template.copy()

    # 日付時刻
    data["date_time"] = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # アプリID
    app_id = random.choice(app_id_list)
    data["app_id"] = app_id

    # モデル
    model = random.choice(model_list)
    data["ai_response"]["model"] = model

    # prompt_tokens
    prompt_tokens = random.randint(prompt_tokens_min, prompt_tokens_max)
    data["ai_response"]["usage"]["prompt_tokens"] = prompt_tokens

    # completion_tokens
    completion_tokens = random.randint(completion_tokens_min, completion_tokens_max)
    data["ai_response"]["usage"]["completion_tokens"] = completion_tokens

    # データリストに追加
    data_list.append(data)

    # 次の5分へ
    current_time += datetime.timedelta(minutes=5)

# データをJSON形式でファイルに出力
with open(output_filename, "w") as f:
    json.dump(data_list, f, indent=4)
