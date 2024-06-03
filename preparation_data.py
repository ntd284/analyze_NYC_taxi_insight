# preparation_data.py

import os
from io import BytesIO
import pandas as pd
from minio import Minio

# Configuration
file_path = "data"
client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="123456789",
    secure=False
)

# Step 1: Merge main parquet table
all_files = os.listdir(file_path)
dataframes = [pd.read_parquet(os.path.join(file_path, file)) for file in all_files]
merged_data_df = pd.concat(dataframes, ignore_index=True)
merged_data_df = merged_data_df.head(150000)
print("Merge successfully")

# Step 2: Merge with taxi zone lookup
taxi_lookup_path = "output_data/taxi_lookup.csv"
df_lookup = pd.read_csv(taxi_lookup_path)

# Merge for pickup locations
merged_data_df = merged_data_df.merge(df_lookup, left_on="PULocationID", right_on="LocationID")
merged_data_df = merged_data_df.drop(columns=['PULocationID', 'LocationID', 'Borough', 'service_zone', 'zone'])
merged_data_df = merged_data_df.rename(columns={'longitude': 'pickup_longitude', 'latitude': 'pickup_latitude'})

# Merge for dropoff locations
merged_data_df = merged_data_df.merge(df_lookup, left_on="DOLocationID", right_on="LocationID")
merged_data_df = merged_data_df.drop(columns=['DOLocationID', 'LocationID', 'Borough', 'service_zone', 'zone'])
merged_data_df = merged_data_df.rename(columns={'longitude': 'dropoff_longitude', 'latitude': 'dropoff_latitude'})

# Drop rows with missing values
merged_data_df = merged_data_df.drop(columns=['Unnamed: 0_x','Unnamed: 0_y']).dropna()

print(merged_data_df.head(10))
# Step 3: Convert to parquet
parquet_buffer = BytesIO()
merged_data_df.to_parquet(parquet_buffer, engine='pyarrow')
parquet_buffer.seek(0)
buffer_length = parquet_buffer.getbuffer().nbytes
print('Convert successfully')

# Step 4: Create storage in Minio
raw_bucket_name = "uberstorage"
if not client.bucket_exists(raw_bucket_name):
    client.make_bucket(raw_bucket_name)
    print(f"Bucket {raw_bucket_name} created successfully.")

# Upload the parquet file to Minio
client.put_object(
    raw_bucket_name,
    'raw/uber.parquet',
    data=parquet_buffer,
    length=buffer_length,
    content_type='application/csv'
)
print("Load into storage successfully")

# Step 5: Create Delta Lake bucket in Minio
delta_bucket_name = "delta-uber"
if not client.bucket_exists(delta_bucket_name):
    client.make_bucket(delta_bucket_name)
    print(f"Bucket {delta_bucket_name} created successfully.")
