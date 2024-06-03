from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from delta import *
import pandas as pd
# start spark session

jars = "libs/hadoop-aws-3.3.4.jar,libs/postgresql-42.2.20.jar,libs/aws-java-sdk-bundle-1.12.260.jar"
builder = SparkSession.builder \
    .appName('uber_analyst') \
    .config("spark.executor.memory", "8g") \
    .config("spark.driver.memory", "8g") \
    .config("spark.dynamicAllocation.enabled", "true") \
    .config("spark.dynamicAllocation.minExecutors", "1") \
    .config("spark.dynamicAllocation.maxExecutors", "10") \
    .config("spark.shuffle.spill", "true") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
    .config("spark.jars", jars) \
    .config("spark.sql.debug.maxToStringFields", 1000)


spark = configure_spark_with_delta_pip(builder, extra_packages=["org.apache.hadoop:hadoop-aws:3.3.4"]).getOrCreate()
sc = spark.sparkContext
# Set the MinIO access key, secret key, endpoint, and other configurations
sc._jsc.hadoopConfiguration().set("fs.s3a.access.key", "admin")
sc._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "123456789")
sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://localhost:9000")
sc._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
sc._jsc.hadoopConfiguration().set("fs.s3a.connection.ssl.enabled", "false")
sc._jsc.hadoopConfiguration().set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
sc._jsc.hadoopConfiguration().set("fs.s3a.connection.ssl.enabled", "false")

url = "jdbc:postgresql://localhost:5433/uber_db"
user = "postgres"
password = "postgres"
driver =  "org.postgresql.Driver"
table =  "uber"

inputPath = "s3a://uberstorage/raw/uber.parquet"
uber_df = spark.read \
    .format('parquet') \
    .option("header", "true") \
    .option('inferSchema','true') \
    .parquet(inputPath)
uber_df = uber_df.drop('_c0')
# uber_df.show()
uber_df= uber_df.withColumn('tpep_pickup_datetime',to_timestamp(col('tpep_pickup_datetime')))
uber_df= uber_df.withColumn('tpep_dropoff_datetime',to_timestamp(col('tpep_dropoff_datetime')))
uber_df= uber_df.withColumn('tpep_dropoff_datetime',to_timestamp(col('tpep_dropoff_datetime')))

uber_df = uber_df.dropDuplicates()
uber_df = uber_df.withColumn("tripid",monotonically_increasing_id())

datetime_dim = uber_df.select('tpep_pickup_datetime','tpep_dropoff_datetime')
datetime_dim = datetime_dim.withColumn("datetime_id", monotonically_increasing_id())

datetime_dim = datetime_dim.withColumn("pickup_hour",hour(col('tpep_pickup_datetime')))
datetime_dim = datetime_dim.withColumn("pickup_day",dayofmonth(col('tpep_pickup_datetime')))
datetime_dim = datetime_dim.withColumn("pickup_month",month(col('tpep_pickup_datetime')))
datetime_dim = datetime_dim.withColumn("pickup_weekday",dayofweek(col('tpep_pickup_datetime')))


datetime_dim = datetime_dim.withColumn("dropoff_hour",hour(col('tpep_dropoff_datetime')))
datetime_dim = datetime_dim.withColumn("dropoff_day",dayofmonth(col('tpep_dropoff_datetime')))
datetime_dim = datetime_dim.withColumn("dropoff_month",month(col('tpep_dropoff_datetime')))
datetime_dim = datetime_dim.withColumn("dropoff_weekday",dayofweek(col('tpep_dropoff_datetime')))
datetime_dim = datetime_dim.select('datetime_id','tpep_pickup_datetime','pickup_hour',
                                    'pickup_day','pickup_month','pickup_weekday',
                                    'tpep_dropoff_datetime','dropoff_hour',
                                    'dropoff_day','dropoff_month','dropoff_weekday')

pickup_location_dim = uber_df.select('pickup_latitude','pickup_longitude')
pickup_location_dim = pickup_location_dim.withColumn('pickup_location_id',monotonically_increasing_id())
pickup_location_dim = pickup_location_dim.select('pickup_location_id','pickup_latitude','pickup_longitude')

dropoff_location_dim = uber_df.select('dropoff_latitude','dropoff_longitude')
dropoff_location_dim = dropoff_location_dim.withColumn('dropoff_location_id',monotonically_increasing_id())
dropoff_location_dim = dropoff_location_dim.select('dropoff_location_id','dropoff_latitude','dropoff_longitude')
# dropoff_location_dim.show()
payment_type_names = {
    1:"Credit card",
    2:"Cash",
    3:"No charge",
    4:"Dispute",
    5:"Unknown",
    6:"Voided trip"
}

def map_payment_type(payment_type):
    return payment_type_names.get(payment_type, "Unknown")

map_payment_type_udf = udf(map_payment_type, StringType())
payment_type_dim = uber_df.select('payment_type')
payment_type_dim = payment_type_dim.withColumn('payment_type_id',monotonically_increasing_id())
payment_type_dim = payment_type_dim.withColumn('payment_type_name',map_payment_type_udf(col('payment_type')))
payment_type_dim = payment_type_dim.select('payment_type_id','payment_type','payment_type_name')
# print(uber_df)

rate_code_name = {
    1:"Standard rate",
    2:"JFK",
    3:"Newark",
    4:"Nassau or Westchester",
    5:"Negotiated fare",
    6:"Group ride",
}

def map_rate_code_type(RatecodeID):
    return rate_code_name.get(RatecodeID, "Unknown")

map_rate_code_udf = udf(map_rate_code_type, StringType())
rate_code_dim = uber_df.select('RatecodeID')
rate_code_dim = rate_code_dim.withColumn('rate_code_id', monotonically_increasing_id())
rate_code_dim = rate_code_dim.withColumn('rate_code_name',map_rate_code_udf(col('RatecodeID')))
rate_code_dim = rate_code_dim.select('rate_code_id','RatecodeID','rate_code_name')

passenger_count_dim = uber_df.select('passenger_count')
passenger_count_dim = passenger_count_dim.withColumn('passenger_count_id',monotonically_increasing_id())
passenger_count_dim = passenger_count_dim.select('passenger_count_id','passenger_count')

trip_distance_dim = uber_df.select('trip_distance')
trip_distance_dim = trip_distance_dim.withColumn('trip_distance_id',monotonically_increasing_id())
trip_distance_dim = trip_distance_dim.select('trip_distance_id','trip_distance')

fact_table = uber_df.join(datetime_dim, datetime_dim.datetime_id == uber_df.tripid , how='inner') \
                    .join(pickup_location_dim, pickup_location_dim.pickup_location_id == uber_df.tripid , how='inner') \
                    .join(dropoff_location_dim, dropoff_location_dim.dropoff_location_id == uber_df.tripid , how='inner') \
                    .join(passenger_count_dim, passenger_count_dim.passenger_count_id == uber_df.tripid , how='inner') \
                    .join(trip_distance_dim, trip_distance_dim.trip_distance_id == uber_df.tripid , how='inner') \
                    .join(rate_code_dim, rate_code_dim.rate_code_id == uber_df.tripid , how='inner') \
                    .join(payment_type_dim, payment_type_dim.payment_type_id == uber_df.tripid , how='inner') 
fact_table = fact_table.select('vendorid','datetime_id','pickup_location_id','dropoff_location_id','passenger_count_id','trip_distance_id','rate_code_id','payment_type_id'
                               ,'fare_amount','extra','mta_tax','tip_amount','tolls_amount','improvement_surcharge','total_amount')
list_table = ['fact_table','datetime_dim','pickup_location_dim','dropoff_location_dim','passenger_count_dim','trip_distance_dim','rate_code_dim','payment_type_dim']
print(fact_table.count())
table_dataframes = {
    'fact_table': fact_table,
    'datetime_dim': datetime_dim,
    'pickup_location_dim': pickup_location_dim,
    'dropoff_location_dim': dropoff_location_dim,
    'passenger_count_dim': passenger_count_dim,
    'trip_distance_dim': trip_distance_dim,
    'rate_code_dim': rate_code_dim,
    'payment_type_dim': payment_type_dim
}
minio_bucket = "delta-uber"

for table_name in list_table:
    dataframe = table_dataframes.get(table_name)
    if dataframe:
        # dataframe_postgresql = dataframe.write \
        # .format("jdbc") \
        # .option("url", url) \
        # .option("dbtable", table_name) \
        # .option("user", user) \
        # .option("password", password) \
        # .option("driver", driver) \
        # .mode("overwrite") \
        # .save()
        # print(f"save {table_name} into postgresql completely")

        dataframe_deltalake =  dataframe.write \
            .format("delta") \
            .mode("overwrite") \
            .save(f"s3a://{minio_bucket}/uber/{table_name}")
        print(f"save {table_name} in minio storage completely")
        
        # uber_df = spark \
        # .read \
        # .format('delta') \
        # .load(f"s3a://{minio_bucket}/uber/{table_name}")
        # uber_df.show()



