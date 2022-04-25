# create the output path in minio
BUCKET_NAME = 'testbucket'
FILE_NAME = 'username'

# setup the connection
from pyarrow import fs
s3 = fs.S3FileSystem(endpoint_override='127.0.0.1:9000',access_key='exampleuser', 
    secret_key='somepassword',  scheme='http')

# read the data from the csv file
from pyarrow import csv
import pyarrow.parquet as pq
pq_output_file = f"{BUCKET_NAME}/{FILE_NAME}.parquet"
with s3.open_input_file(f"{BUCKET_NAME}/{FILE_NAME}.csv") as file:
  table = csv.read_csv(file)
  
  # example query from table
  import pyarrow as pa
  import pyarrow.compute as pc
  value_index = table.column('Identifier')
  row_mask = pc.equal(value_index, pa.scalar(2070, value_index.type))
  selected_table = table.filter(row_mask)
  print(selected_table)
  
  # write the table to minio as parquet file
  pq.write_to_dataset(table=table, root_path=pq_output_file, filesystem=s3) 
