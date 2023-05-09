from pyspark.sql import SparkSession
from pyspark.sql.functions import split, from_json, col, udf
from pyspark.sql.types import StructType, StructField, StringType, FloatType, LongType, TimestampType, DoubleType
import datetime
import uuid

kafka_bootstrap_servers = '192.168.127.38:9093'
topic = 'coin-trades'
keyspace = 'bitcoin'
table = 'trades'

spark = SparkSession.builder.appName("PySparkShell") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,com.datastax.spark:spark-cassandra-connector_2.12:3.1.0") \
        .config("spark.cassandra.connection.host", "192.168.127.38") \
        .config("spark.cassandra.connection.port", "9042") \
        .config("spark.cassandra.auth.username", "root") \
        .config("spark.cassandra.auth.password", "root") \
        .getOrCreate()

schema = StructType([
    StructField("exchange", StringType(), True),
    StructField("base", StringType(), True),
    StructField("quote", StringType(), True),
    StructField("direction", StringType(), True),
    StructField("price", DoubleType(), True),
    StructField("volume", DoubleType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("price_usd", DoubleType(), True),
])

@udf(returnType=StringType())
def generate_uuid():
    return str(uuid.uuid4())

@udf(returnType=StringType())
def convert_timestamp(timestamp_ms):
    timestamp_s = timestamp_ms / 1000
    dt = datetime.datetime.fromtimestamp(timestamp_s)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# maxOffsetsPerTrigger: batch interval
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "False") \
    .option("subscribe", topic) \
    .option("kafka.group.id", "spark_test") \
    .option("maxOffsetsPerTrigger", "100") \
    .load()
#df = df.selectExpr("CAST(value AS STRING)")
# data.* 이 schema에 정의된 대로 개별칼럼으로 분리해줌(안그러면 data라는 같은 하나의 칼럼 이름으로 나옴)
df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

df = df.withColumn('uuid', generate_uuid())
df = df.withColumn("timestamp", convert_timestamp(col('timestamp').cast("double")))
# df = df.withColumnRenamed('priceUsd', 'price_usd')

def save_to_cassandra(batch_df, epoch_id):
    batch_df.write \
        .format("org.apache.spark.sql.cassandra") \
        .mode("append") \
        .option("keyspace", keyspace) \
        .option("table", table) \
        .save()
"""
query = df \
    .writeStream \
    .format("console") \
		.option("truncate", "false") \
    .start()
"""
query = df \
    .writeStream \
    .outputMode("append") \
    .foreachBatch(save_to_cassandra) \
    .start()
query.awaitTermination()
