from pyspark.sql import SparkSession
from pyspark.sql.functions import split, from_json, col, udf, explode
from pyspark.sql.types import StructType, StructField, StringType, FloatType, LongType, TimestampType, DoubleType, MapType
import datetime
import uuid

kafka_bootstrap_servers = '192.168.127.38:9092'
topic = 'coin-prices'
keyspace = 'bitcoin'
table = 'prices'
kafka_group = 'coin-prices'

spark = SparkSession.builder.appName("PySparkShell") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,com.datastax.spark:spark-cassandra-connector_2.12:3.1.0") \
        .config("spark.cassandra.connection.host", "192.168.127.38") \
        .config("spark.cassandra.connection.port", "9042") \
        .config("spark.cassandra.auth.username", "root") \
        .config("spark.cassandra.auth.password", "root") \
        .getOrCreate()

schema = MapType(StringType(), StringType())
@udf(returnType=StringType())
def generate_uuid():
    return str(uuid.uuid4())

@udf(returnType=StringType())
def generate_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_to_cassandra(batch_df, epoch_id):
    batch_df.write \
        .format("org.apache.spark.sql.cassandra") \
        .mode("append") \
        .option("keyspace", keyspace) \
        .option("table", table) \
        .save()

# maxOffsetsPerTrigger: batch interval
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("failOnDataLoss", "False") \
    .option("subscribe", topic) \
    .option("kafka.group.id", kafka_group) \
    .option("maxOffsetsPerTrigger", "100") \
    .load()

    #.option("startingOffsets", "earliest") \
#df = df.selectExpr("CAST(value AS STRING)")
# data.* 이 schema에 정의된 대로 개별칼럼으로 분리해줌(안그러면 data라는 같은 하나의 칼럼 이름으로 나옴)
df = df.select(from_json(col("value").cast("string"), schema).alias("data"))
df = df.select(explode(col("data")).alias("base", "price"))
df = df.withColumn('uuid', generate_uuid())
df = df.withColumn('timestamp', generate_timestamp())
#df = df.withColumn("timestamp", convert_timestamp(col('timestamp').cast("double")))
# df = df.withColumnRenamed('priceUsd', 'price_usd')

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

