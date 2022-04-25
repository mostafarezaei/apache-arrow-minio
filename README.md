# Connecting MinIO to Apache Arrow
How to communicate between Apache Arrow and MinIO

## About Apache Arrow
Apache Arrow improves the speed of data analytics by creating a standard columnar memory format that any computer language can understand. 
Apache Arrow performance allows for the transfer of data without the cost of serialization (the process of translating data into a format that can be stored). Apache Arrow is a standard that can be implemented by any computer program that processes memory data.

## About MinIO
MinIO is pioneering high performance object storage for the era of the hybrid cloud. The software-defined, Amazon S3-compatible object storage system has been voted the “Most Impactful Open Source Project” by Strata/O’Reilly and is run by more than half of the Fortune 500. With more than 545M Docker pulls, MinIO is the fastest-growing private cloud object storage company. 

## Apache Arrow to Connect to MinIO
Many applications require the provision of large amounts of data, usually processed by services such as hadoop or spark, to other services. This can easily be done by Apache Arrow. MinIO allows access to files and buckets via S3. This way we can read or write files in Arrow.

Obviously this is just an example and you can start this way for your usecase. The following is a step by step tutorial on how to integrate the two:

1. Run the Arrow through docker:
Note: Running MinIO in standalone mode is intended for early development and evaluation. For production clusters, deploy a Distributed MinIO deployment.

    MinIO needs a persistent volume to store configuration and application data. To create a MinIO container with persistent storage, you need to map local persistent directories from the host OS to virtual config. To do this, run the below commands

    ```
        mkdir -p ~/minio/data

        docker run \
          -p 9000:9000 \
          -p 9001:9001 \
          --name minio1 \
          -v ~/minio/data:/data \
          -e "MINIO_ROOT_USER=exampleuser" \
          -e "MINIO_ROOT_PASSWORD=somepassword" \
          quay.io/minio/minio server /data --console-address ":9001"
    ```

    The command creates a new local directory ~/minio/data in your user home directory. It then starts the MinIO container with the -v argument to map the local path (~/minio/data) to the specified virtual container directory (/data). When MinIO writes data to /data, that data is actually written to the local path ~/minio/data where it can persist between container restarts.

2. You can use http://127.0.0.1:9001 to access the MinIO console. Note that the api port in this example is 9000. 

    ![Alt text](docs/minio-console.png?raw=true "MinIO Console")

    Open the MinIO Console and create a bucket called testbucket. Now upload the username.csv file to this bucket.

3. Install the pyarrow python module through pip. This could be done using below command:
    
    ```bash
    pip3 install pyarrow
    ```

4. The following code first reads the username.csv file loaded in the bucket. The result is a table with the following structure:

    Field Name | Data Type
    --- | ---
    Username | string 
    Identifier | int64
    First name | string 
    Last name  | string 

    In the next step, a query is written on this table that filters on the Identifier field. The result is printed to the console.

    Now the desired table is written as parquet in the same bucket.

    ```python
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
    ```