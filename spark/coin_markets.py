import uuid
from datetime import datetime
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, FloatType, LongType, DoubleType
from google.cloud import storage
from google.oauth2 import service_account
import pandas as pd

# 파이썬 코드에서 환경변수 설정
def downloads_markets_from_gcs(bucket_name, source_blob_name, destination_file_name) -> None:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

@udf(returnType=StringType())
def generate_uuid():
    return str(uuid.uuid4())
@udf(returnType=StringType())
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main() -> None:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/srhwang/Project/boot_camp/zoomcamp/coin-385610-ab42e26c1279.json"
    current_date = datetime.now().strftime("%Y-%m-%d")

    bucket_name = "coin-bucket"
    source_blob_name = f"{current_date}_markets.csv"
    destination_file_name = f"{current_date}_markets.csv"

    downloads_markets_from_gcs(bucket_name, source_blob_name, destination_file_name)

    ss = SparkSession.builder \
        .appName("markets by coin") \
        .config("spark.jars.packages", "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.30.0") \
        .getOrCreate()

    schema = StructType([
        StructField("exchange", StringType(), True),
        StructField("base", StringType(), True),
        StructField("quote", StringType(), True),
        StructField("base_symbol", StringType(), True),
        StructField("quote_symbol", StringType(), True),
        StructField("volume_usd_24_hr", DoubleType(), True),
        StructField("price_usd", DoubleType(), True),
        StructField("volume_percent", DoubleType(), True),
    ])

    df = ss.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(destination_file_name)

    df = ss.createDataFrame(df.rdd, schema=schema)
    df = df.withColumn("uuid", generate_uuid())
    df = df.withColumn("timestamp", generate_timestamp())

    project_id = "coin-385610"
    dataset_id = "coin"
    table_id = "markets"

    df = df.withColumn("volume_usd_24_hr", df['volume_usd_24_hr'].cast(FloatType()))
    df = df.withColumn("price_usd", df['price_usd'].cast(FloatType()))
    df = df.withColumn("volume_percent", df['volume_percent'].cast(FloatType()))
    
    df.write \
        .format("bigquery") \
        .option("table", f"{project_id}:{dataset_id}.{table_id}") \
        .option("writeMethod", "direct") \
        .mode("append") \
        .save("dataset.table")
    
if __name__ == "__main__":
    main()

