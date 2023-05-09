from datetime import datetime, timedelta
from typing import Optional
import logging
import requests

from google.cloud import storage
import pandas as pd

def collect_market_data() -> pd.DataFrame:
    coins = ["bitcoin","ethereum","tether","binance-coin",
            "usd-coin","xrp","cardano","dogecoin","polygon","solana"]
    market_data_concated = pd.DataFrame()
    for coin in coins:
        market_data = fetch_market_data_by_coin(coin)
        if market_data is not None:
            market_data_concated = pd.concat([market_data_concated, market_data], ignore_index=True)

    return market_data_concated

def fetch_market_data_by_coin(coin: str) -> Optional[pd.DataFrame]:
    url = f'http://api.coincap.io/v2/assets/{coin}/markets'
    response = requests.get(url)

    if response.status_code == 200:
        res_data = response.json()
        market_data = pd.DataFrame(res_data['data'])
        return market_data
    else:
        logging.error(f"API 요청 실패, 상태 코드: {response.status_code}")
        return None

def upload_dataframe_to_gcs(df: pd.DataFrame, bucket_name: str, destination_blob_name: str) -> None:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    csv_data = df.to_csv(index=False).encode("utf-8")
    blob.upload_from_string(csv_data, content_type="text/csv")

def main() -> None:
    market_data = collect_market_data()
#    current_date = datetime.now().strftime("%Y-%m-%d")
    current_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    bucket_name = "coin-bucket"
    destination_blob_name = f"{current_date}_markets.csv"
    upload_dataframe_to_gcs(market_data, bucket_name, destination_blob_name)

if __name__ == "__main__":
    main()
