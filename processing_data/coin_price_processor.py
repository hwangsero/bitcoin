import json

from pyspark.sql import SparkSession
from pyspark.sql.functions import split, from_json, col, udf, explode, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, FloatType, LongType, TimestampType, DoubleType, MapType
from datetime import datetime
import uuid
from dataclasses import dataclass


@dataclass
class CassandraConfig:
    host: str
    port: str
    username: str
    password: str

@dataclass
class KafkaConsumerConfig:
    bootstrap_servers: str
    consumer_group: str
    topic: str


class CoinPriceProcessor:
    def __init__(self, cassandra_config: CassandraConfig, kafka_consumer_config: KafkaConsumerConfig):
        self.cassandra_config = cassandra_config
        self.kafka_consumer_config = kafka_consumer_config
        self.spark_session = self.create_spark_session()
        self.schema = MapType(StringType(), StringType())

    @staticmethod
    @udf(returnType=StringType())
    def generate_uuid():
        return str(uuid.uuid4())

    @staticmethod
    @udf(returnType=TimestampType())
    def generate_timestamp():
        return datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

    def create_spark_session(self) -> SparkSession:
        spark_session = SparkSession.builder.appName("coin-prices") \
            .config("spark.jars.packages",
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,com.datastax.spark:spark-cassandra-connector_2.12:3.1.0") \
            .config("spark.cassandra.connection.host", self.cassandra_config.host) \
            .config("spark.cassandra.connection.port", self.cassandra_config.port) \
            .config("spark.cassandra.auth.username", self.cassandra_config.username) \
            .config("spark.cassandra.auth.password", self.cassandra_config.password) \
            .getOrCreate()
        return spark_session

    def read_stream_from_kafka(self) -> DataFrame:
        df = self.spark_session \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_consumer_config.bootstrap_servers) \
            .option("kafka.group.id", self.kafka_consumer_config.consumer_group) \
            .option("subscribe", self.kafka_consumer_config.topic) \
            .option("failOnDataLoss", "False") \
            .option("maxOffsetsPerTrigger", "100") \
            .load()
        return df
    def transform_coin_prices(self, df: DataFrame) -> DataFrame:

        #df = df.selectExpr("CAST(value AS STRING)")
        # data.* 이 schema에 정의된 대로 개별칼럼으로 분리해줌(안그러면 data라는 같은 하나의 칼럼 이름으로 나옴)
        df = df.select(from_json(col("value").cast("string"), self.schema).alias("data"))
        df = df.select(explode(col("data")).alias("base", "price"))
        df = df.withColumn('uuid', CoinPriceProcessor.generate_uuid())
        df = df.withColumn('timestamp', CoinPriceProcessor.generate_timestamp())
        #df = df.withColumn("timestamp", convert_timestamp(col('timestamp').cast("double")))
        # df = df.withColumnRenamed('priceUsd', 'price_usd')
        return df



    def save_batch_to_cassandra(self, batch_df, epoch_id) -> None:
        batch_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .option("keyspace", "bitcoin") \
            .option("table", "prices") \
            .option("ttl", "3600") \
            .save()
    def write_stream_to_cassandra(self, df: DataFrame) -> None:
        query = df \
            .writeStream \
            .outputMode("append") \
            .foreachBatch(self.save_batch_to_cassandra) \
            .start()
        query.awaitTermination()

    def process(self) -> None:
        extract_coin_prices = self.read_stream_from_kafka()
        transformed_coin_prices = self.transform_coin_prices(extract_coin_prices)
        self.write_stream_to_cassandra(transformed_coin_prices)


def load_config(config_path: str):
    with open(config_path, 'r') as f:
        config = json.load(f)
        return config

def main() -> None:
    config = load_config('config.json')
    cassandra_config = CassandraConfig(**config["cassandra_config"])
    kafka_consumer_config = KafkaConsumerConfig(
        bootstrap_servers='192.168.127.38:9092',
        consumer_group='coin-prices-group',
        topic='coin-prices'
    )

    # init, return spark_session
    coin_price_processor = CoinPriceProcessor(cassandra_config, kafka_consumer_config)
    coin_price_processor.process()



    # s,c


    # read, return df s, k
    # maxOffsetsPerTrigger: batch interval

    # transform, return df
    #.option("startingOffsets", "earliest") \

    """
    query = df \
        .writeStream \
        .format("console") \
        .option("truncate", "false") \
        .start()
    """


if __name__ == "__main__":
    main()
