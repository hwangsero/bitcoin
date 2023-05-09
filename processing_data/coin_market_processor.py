import uuid
import os
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import DataFrame, udf
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, FloatType, LongType, DoubleType
from google.cloud import storage
from dataclasses import dataclass


@dataclass
class MarketDataConfig:
    bucket_name: str
    source_blob_name: str
    destination_file_name: str

@dataclass
class BigqueryConfig:
    project_id: str
    dataset_id: str
    table_id: str

class CoinMarketProcessor:
    def __init__(self, market_data_config: MarketDataConfig, bigquery_config: BigqueryConfig):
        self.market_data_config = market_data_config
        self.bigquery_config = bigquery_config
        self.spark_session = self.create_spark_session()
        self.schema = StructType([
            StructField("exchange", StringType(), True),
            StructField("base", StringType(), True),
            StructField("quote", StringType(), True),
            StructField("base_symbol", StringType(), True),
            StructField("quote_symbol", StringType(), True),
            StructField("volume_usd_24_hr", FloatType(), True),
            StructField("price_usd", FloatType(), True),
            StructField("volume_percent", FloatType(), True),
        ])

    @staticmethod
    @udf(returnType=StringType())
    def generate_uuid():
        return str(uuid.uuid4())

    @staticmethod
    @udf(returnType=TimestampType())
    def generate_timestamp():
        return datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')

    def create_spark_session(self) -> SparkSession:
        spark_session = SparkSession.builder \
            .appName("markets by coin") \
            .config("spark.jars.packages", "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.30.0") \
            .getOrCreate()
        return spark_session

    def downloads_markets_from_gcs(self) -> None:
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.market_data_config.bucket_name)
        blob = bucket.blob(self.market_data_config.source_blob_name)
        blob.download_to_filename(self.market_data_config.destination_file_name)

    def read_market_data(self) -> DataFrame:
        df = self.spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(self.market_data_config.destination_file_name)
        return df

    def transform_market_data(self, df: DataFrame) -> DataFrame:
        df = self.spark_session.createDataFrame(df.rdd, schema=self.schema)
        df = df.withColumn("uuid", CoinMarketProcessor.generate_uuid())
        df = df.withColumn("timestamp", CoinMarketProcessor.generate_timestamp())
        return df
        """ 
        df = df.withColumn("volume_usd_24_hr", df['volume_usd_24_hr'].cast(FloatType()))
        df = df.withColumn("price_usd", df['price_usd'].cast(FloatType()))
        df = df.withColumn("volume_percent", df['volume_percent'].cast(FloatType()))
        """

    def write_to_bigquery(self, df: DataFrame) -> None:
        df.write \
            .format("bigquery") \
            .option("table", f"{self.bigquery_config.project_id}" 
                             f":{self.bigquery_config.dataset_id}"
                             f".{self.bigquery_config.table_id}") \
            .option("writeMethod", "direct") \
            .mode("append") \
            .save("dataset.table")

    def process(self) -> None:
        self.downloads_markets_from_gcs()
        extract_markets = self.read_market_data()
        transform_markets = self.transform_market_data(extract_markets)
        self.write_to_bigquery(transform_markets)

def main() -> None:
    current_date = datetime.now().strftime("%Y-%m-%d")

    market_data_config = MarketDataConfig(
        bucket_name="coin-bucket",
        source_blob_name=f"{current_date}_markets.csv",
        destination_file_name=f"csv/{current_date}_markets.csv"
    )
    bigquery_config = BigqueryConfig(
        project_id="coin-385610",
        dataset_id="coin",
        table_id="markets"
    )

    coin_market_processor = CoinMarketProcessor(market_data_config, bigquery_config)
    coin_market_processor.process()


if __name__ == "__main__":
    main()
