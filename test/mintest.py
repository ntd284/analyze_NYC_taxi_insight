# from minio import Minio

# client = Minio(
#     "localhost:9000",
#     access_key="admin",
#     secret_key="123456789",
#     secure=False
# )

# bucket_name = "uberbackup"

# found = client.bucket_exists(bucket_name)
# if not found:
#     client.make_bucket(bucket_name)

# destination_file = 'uber.txt'
# source_file = 'data/uber_data.csv'

# client.fput_object(bucket_name, destination_file, source_file)

from minio import Minio
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pandas as pd
client = Minio(
    "localhost:9000",
    access_key='admin',
    secret_key='123456789',
    secure=False
)

minio_bucket = "delta"

found = client.bucket_exists(minio_bucket)
if not found:
    client.make_bucket(minio_bucket)

coffee_csv = 'coffee_sales.csv'

obj = client.get_object(
    "uberstorage",
    "raw/uber.csv",
)
df = pd.read_csv(obj)
print(df)
# coffee_df = spark.read.format('csv').option('header', 'true').option('inferSchema', 'true').load(coffee_csv)